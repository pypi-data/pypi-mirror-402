RFC 1: Cacheguard File Conventions  
Author: Michael Buckley
Date: November 13, 2025  
Status: Draft  

# CACHEGUARD FILE CONVENTIONS

## ABSTRACT

This document outlines the expected standards for Cacheguard's operations when it comes to default behavior on filenames and directory structures.  The standardization is driven by anticipation of external tool use and interoperability.

## Table of Contents

- [Abstract](#abstract)
- [File Conventions](#file-conventions)
  - [File Access](#file-access)
  - [Extensions](#extensions)
  - [Names](#names)
- [Directory Conventions](#directory-conventions)
  - [Default Behaviors](#default-behaviors)
  - [Environment Variable](#environment-variable)
- [Overriding Defaults](#overriding-defaults)
- [References](#references)
- [Appendices](#appendices)
  - [Environment Variables](#environment-variables)

## File Conventions

### File Access

All files are written to the filesystem after encrypted by Sops.  All Sops-based tooling is compatible with the resulting files as they are Sops files.  They can be decrypted using Sops.  Furthermore, they are safe to commit as they are secured.

This module does not write anything to the filesystem that is not encrypted.

### Extensions

The two major cache types are Key and Text Caches and as such, have default filenames that align with them:

- `*.keys.sops`  
- `*.text.sops`

Both types are Sops binary blobs, meaning the files are completely encrypted and the keys are not visible without decryption.

```
NOTE:
Key Caches are also written as a string, however, are a JSON string.
For human-readable names, use JSON format instead of the default binary format.
```

### Names

Names do not require the same level of standardization from a tool-use perspective, as searching for extensions suitably filters the bulk of actions.

However, some defaults are implemented when no user definitions were given at runtime.  The default filename will be:

`<Cache Type>-<ISO8601 Timestamp>.<Extension>`

With the example being:

`text-2025-11-13T07-21-32.text.sops`

For an unnamed Text Cache created at time of writing.  The timestamp will be created at Cache object creation.

The name is completely overridable with the text replaceable and the timestamp is an optional boolean parameter.

## Directory Conventions

### Default Behaviors

The standard directory that will be used is `.cacheguard` at the root of the program or project.

### Environment Variable

- Names
- Structure
- Envars


## Overriding Defaults

All default behavior is overridable and can be configured to suit the user's need.  As listed, environment variables are considered by the program when running.  Likewise, any adjacent programs should consider them as well.

## References

Sops - https://getsops.io/  
ISO8601 - https://www.isotc154.org/posts/2019-08-27-introduction-to-the-new-8601/  

## Appendices

### Environment Variables

- TBD