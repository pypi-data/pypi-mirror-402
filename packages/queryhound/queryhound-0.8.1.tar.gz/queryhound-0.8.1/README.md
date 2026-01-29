# QueryHound 🐾

QueryHound sniffs out slow queries, COLLSCANs, and other patterns in MongoDB logs.

Full documentation: https://dmcna005.github.io/queryhound_qh/

Get started:

```bash
pip install -U queryhound
qh --help
```

Stream logs from a pipe (stdin):

```bash
# Explicit stdin
tail -f /var/log/mongodb/mongod.log | qh - --slow

# Auto-detect piped input
zcat mongo.log.gz | qh --error
```
