# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | yes       |
| 0.5.x   | security fixes only |
| < 0.5   | no        |

## Threat Model

AI Photo Restoration Studio is an offline desktop application. It does
not phone home. There is no account system, no cloud sync, and no
auto-update that pulls arbitrary code.

The realistic attack surfaces are:

1. **Model file supply chain.** A malicious `.onnx` file can, in
   principle, exploit a parser bug in ONNX Runtime. We mitigate by:
   - pinning every model by SHA256 in `config/model_manifest.json`
   - refusing to load weights whose hash doesn't match
   - running inference in a subprocess with a restricted working dir
2. **Image file parsers.** We use Pillow + `pillow-heif`. Malformed
   HEIC/JPEG2000 can crash the loader. Keep Pillow up to date.
3. **Plugin directory.** `app/handlers/` is scanned only from the
   installed package, not from user-writable paths. There is no
   plugin-from-disk mechanism by design.

## Reporting a Vulnerability

Email `security@photo-restoration-studio.dev` (PGP key in `docs/`).
Please do not open public issues for exploitable bugs. Response within
72 hours, patch within 14 days for confirmed high-severity issues.

## Out of Scope

- Crashes caused by corrupted input images that we already warn about.
- GPU driver bugs (report to vendor).
- Anything requiring an attacker to already have local code execution.