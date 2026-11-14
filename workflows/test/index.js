// Lets `node --test workflows/test` work on Node 24, where a directory argument
// is loaded as a module. The tests themselves are in the *.test.mjs files.
import('./triage.test.mjs');
import('./email-intake.test.mjs');
