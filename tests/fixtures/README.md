# Test fixtures

Real `.msg` files can only be produced by Outlook, so they are not generated in
code. When adding a binary fixture here, follow two rules:

1. **Synthetic data only.** Never commit real or confidential email content.
   Use made-up names, addresses, and bodies.
2. **Document what's interesting.** Add a line below describing why the fixture
   exists, so a future contributor knows what it exercises.

## How to create one

1. In Outlook, compose a message with the characteristics you want to test
   (an inline image, a non-ASCII subject, an embedded message, and so on).
2. Save it as `Outlook Message Format - Unicode` (`.msg`).
3. Drop it in this folder and add a note to the list below.

## The reader's unit coverage

The reader is covered without binary fixtures by a faithful stand-in that mimics
the parser's attribute surface (see `tests/unit/test_reader.py`). The transforms,
pipeline, batch, determinism, and CLI are covered with synthetic records written
to real temporary directories. Binary fixtures added here extend that with
real-file integration coverage.

## Fixtures

_None committed yet._ Planned, when generated:

- `simple.msg` — plain text + HTML body, no attachments.
- `with-attachments.msg` — a couple of regular file attachments.
- `inline-images.msg` — inline images referenced by `cid:`.
- `nested-msg.msg` — a message with another message attached.
- `meeting-request.msg` — a calendar/meeting item.
