// Lets `node --test workflows/test` work on Node 24, where a directory argument
// is loaded as a module. The tests themselves are in triage.test.mjs.
import('./triage.test.mjs');
