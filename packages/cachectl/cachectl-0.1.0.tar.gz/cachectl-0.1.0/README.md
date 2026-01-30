# cachectl

Configure cache directories for pnpm, npm, yarn, pip, poetry, and uv.

## Usage

Interactive mode:

```
cachectl
```

Set a cache path (non-interactive):

```
cachectl set pnpm D:\cache\pnpm
cachectl set uv D:\cache\uv
```

Query current settings:

```
cachectl query
cachectl get pnpm
```

Migrate existing cache to a new path:

```
cachectl migrate yarn D:\cache\yarn
```
