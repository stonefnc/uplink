// Offline tests for workflows/uplink-email-intake.json.
// Run with: node --test workflows/test

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const workflowsDir = path.resolve(here, '..');
const rawText = fs.readFileSync(path.join(workflowsDir, 'uplink-email-intake.json'), 'utf8');
const workflow = JSON.parse(rawText);
const node = (name) => workflow.nodes.find((n) => n.name === name);

async function toTickets(mails) {
  const sandbox = { $input: { all: () => mails.map((json) => ({ json })) }, console };
  const script = new vm.Script(`(async function () {\n${node('Email to ticket').parameters.jsCode}\n})()`);
  const result = await script.runInContext(vm.createContext(sandbox), { timeout: 5000 });
  return JSON.parse(JSON.stringify(result)).map((item) => item.json.ticket);
}

const mail = {
  from: 'requester@example.org',
  to: 'helpdesk@example.org',
  subject: 'Printer keeps jamming',
  date: 'Mon, 02 Mar 2026 09:15:00 -0500',
  textPlain: 'It jams on every job.\n\nThanks.',
  textHtml: '<p>ignored when plain text exists</p>',
  metadata: { 'message-id': '<abc123@example.org>' },
};

describe('email intake workflow structure', () => {
  test('name, fixed id, inactive, no instance data', () => {
    assert.equal(workflow.name, 'Uplink email intake');
    assert.equal(workflow.id, 'UplinkEmail00001');
    assert.equal(workflow.active, false);
    for (const key of ['pinData', 'versionId', 'meta', 'staticData']) assert.ok(!(key in workflow));
  });

  test('trigger, map, send, in that order', () => {
    assert.deepEqual(
      workflow.nodes.map((n) => [n.name, n.type]),
      [
        ['Email trigger', 'n8n-nodes-base.emailReadImap'],
        ['Email to ticket', 'n8n-nodes-base.code'],
        ['Send to triage', 'n8n-nodes-base.httpRequest'],
      ]
    );
    const targets = (from) => workflow.connections[from].main[0].map((c) => c.node);
    assert.deepEqual(targets('Email trigger'), ['Email to ticket']);
    assert.deepEqual(targets('Email to ticket'), ['Send to triage']);
  });

  test('trigger reads INBOX, marks mail read, and only references a credential', () => {
    const trigger = node('Email trigger');
    assert.equal(trigger.parameters.mailbox, 'INBOX');
    assert.equal(trigger.parameters.postProcessAction, 'read');
    assert.equal(trigger.parameters.format, 'simple');
    assert.deepEqual(trigger.credentials, { imap: { id: 'UplinkImap000001', name: 'Uplink mailbox' } });
    assert.ok(!/password/i.test(rawText));
  });

  test('send posts the ticket to the triage webhook and does not stop on errors', () => {
    const send = node('Send to triage');
    assert.equal(send.parameters.method, 'POST');
    assert.match(send.parameters.url, /\$env\.UPLINK_INTAKE_URL/);
    assert.match(send.parameters.url, /http:\/\/localhost:5678\/webhook\/ticket/);
    assert.equal(send.parameters.jsonBody, '={{ JSON.stringify($json.ticket) }}');
    assert.equal(send.onError, 'continueRegularOutput');
  });

  test('credential templates match the id the workflow references', () => {
    for (const file of ['imap.example.json', 'imap.test.json']) {
      const [credential] = JSON.parse(fs.readFileSync(path.join(workflowsDir, 'credentials', file), 'utf8'));
      assert.equal(credential.id, 'UplinkImap000001');
      assert.equal(credential.name, 'Uplink mailbox');
      assert.equal(credential.type, 'imap');
    }
  });
});

describe('Email to ticket', () => {
  test('maps subject, plain text and date; channel is email', async () => {
    const [ticket] = await toTickets([mail]);
    assert.deepEqual(Object.keys(ticket), ['id', 'received_at', 'channel', 'subject', 'body']);
    assert.equal(ticket.channel, 'email');
    assert.equal(ticket.subject, 'Printer keeps jamming');
    assert.equal(ticket.body, 'It jams on every job.\n\nThanks.');
    assert.equal(ticket.received_at, '2026-03-02T14:15:00.000Z');
    assert.match(ticket.id, /^E-20260302141500-[0-9a-z]+$/);
  });

  test('the sender address is never passed on', async () => {
    const [ticket] = await toTickets([mail]);
    assert.ok(!JSON.stringify(ticket).includes('requester@example.org'));
  });

  test('id is stable for the same message and differs between messages', async () => {
    const [a, b, c] = await toTickets([mail, mail, { ...mail, metadata: { 'message-id': '<other@example.org>' } }]);
    assert.equal(a.id, b.id);
    assert.notEqual(a.id, c.id);
  });

  test('falls back to text taken from HTML', async () => {
    const [ticket] = await toTickets([
      { ...mail, textPlain: '', textHtml: '<style>p{}</style><p>Wi-Fi is down &amp; out.</p><p>Room 12<br>Building B</p>' },
    ]);
    assert.equal(ticket.body, 'Wi-Fi is down & out.\nRoom 12\nBuilding B');
  });

  test('headers found only in metadata are used', async () => {
    const [ticket] = await toTickets([
      { textPlain: 'Body.', metadata: { subject: 'From metadata', date: 'Mon, 02 Mar 2026 09:15:00 -0500' } },
    ]);
    assert.equal(ticket.subject, 'From metadata');
    assert.equal(ticket.received_at, '2026-03-02T14:15:00.000Z');
  });

  test('missing or bad fields do not throw', async () => {
    const tickets = await toTickets([{}, { subject: 5, date: 'not a date', textPlain: null }]);
    assert.equal(tickets.length, 2);
    for (const ticket of tickets) {
      assert.equal(ticket.subject, '');
      assert.equal(ticket.body, '');
      assert.ok(!Number.isNaN(Date.parse(ticket.received_at)));
    }
  });

  test('one ticket per email', async () => {
    assert.equal((await toTickets([mail, mail, mail])).length, 3);
  });
});
