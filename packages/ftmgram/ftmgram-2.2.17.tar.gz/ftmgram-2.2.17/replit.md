# Ftmgram - Telegram MTProto API Framework

## Overview

Ftmgram is a modern, asynchronous Python framework for interacting with Telegram's MTProto API. It's a fork of Ftmgram that enables developers to build Telegram bots and user clients with an elegant, type-hinted API. The framework abstracts low-level MTProto protocol details while providing full access to Telegram's capabilities through both user accounts and bot identities.

## Recent Changes

- **January 2026**: Renamed project from "pyrogram/pyrotgfork" to "ftmgram/ftmdevtgfork"
  - Directory: `pyrogram/` → `ftmgram/`
  - Package name: `pyrotgfork` → `ftmdevtgfork`
  - All imports now use `import ftmgram` instead of `import pyrogram`
  - Environment variables renamed from `PYROGRAM_*` to `FTMGRAM_*`

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework Design

**Client-Handler Pattern**: The framework uses a central `Client` class that manages connections, authentication, and dispatches updates to registered handlers. Handlers are specialized classes (MessageHandler, CallbackQueryHandler, etc.) that process specific update types using an async callback pattern.

**Event-Driven Architecture**: Updates from Telegram are processed through a dispatcher (`dispatcher.py`) that routes raw MTProto updates to appropriate handler chains. The `StopPropagation` and `ContinuePropagation` exceptions control handler flow.

**Filter System**: A composable filter system (`filters.py`) allows declarative message matching using operators (`&`, `|`, `~`) for combining filter conditions.

### Protocol Layer

**MTProto Implementation**: Custom implementation of Telegram's MTProto 2.0 protocol including:
- Connection management with multiple transport modes (TCP Full, Abridged, Intermediate, obfuscated variants)
- Cryptographic operations using TgCrypto for AES-IGE and CTR modes
- RSA key handling for initial key exchange
- Prime factorization for Diffie-Hellman key agreement

**Code Generation**: The `compiler/` directory contains build-time code generators that:
- Parse TL schema files to generate Python classes for all MTProto types and functions
- Generate error exception classes from CSV definitions
- Output goes to `ftmgram/raw/` (generated at build time via hatch hook)

### Async/Sync Support

The framework is fully async but provides synchronous wrappers (`sync.py`) for convenience. Uses `asyncio` with thread pool executors for CPU-bound crypto operations.

### Enums and Type System

Extensive use of Python enums (`ftmgram/enums/`) for type-safe constants covering chat types, message types, user statuses, parse modes, and more. All methods and types are fully type-hinted.

## External Dependencies

### Required Services

- **Telegram API**: Requires API ID and API Hash from https://my.telegram.org for authentication
- **Telegram Data Centers**: Connects to Telegram's MTProto servers (production or test mode)

### Key Python Dependencies

- **TgCrypto**: High-performance C library for MTProto encryption (AES-IGE, AES-CTR) - optional but recommended
- **hatchling**: Build system with custom hook for code generation

### Documentation

- **Sphinx**: Documentation generator with Furo theme
- **sphinx-copybutton**: Code block copy functionality

### Development/Testing

- **pytest**: Test framework for unit tests (see `tests/` directory)