# Mobile Agent

Handles Flutter mobile tasks. **This boilerplate ships no mobile app** — this guide applies only after a project adds one under `apps/mobile*/`. If none exists and the user asks for mobile work, confirm scope before scaffolding.

---

## Step 0 — Read AI_GUIDE

Read `AI_GUIDE.md` in the active `apps/mobile*/` folder if it exists. It gives the project structure, file locations, and critical rules.

---

## Step 1 — Detect Active Mobile Stack

| Indicator file | Stack |
|----------------|-------|
| `pubspec.yaml` + `lib/` | Flutter (Dart) |

Folder names are free-form (`mobile*`) — always detect by content, not by name.

---

## Step 2 — Backend contract

The backend (`apps/backend`, port 8020) returns tokens in the response body (`data.auth.accessToken` / `refreshToken`) as well as httpOnly cookies, so mobile clients use `Authorization: Bearer <access>` and `POST /auth/refresh` with `Authorization: Bearer <refresh>`. Every response uses the `{metaData, data}` envelope (see `docs/api-spec.md`).

---

## Architecture Pattern

Flutter projects follow **MVVM + Provider**:

| Layer | Role |
|-------|------|
| `view/` | Stateless widgets — render only, no logic |
| `viewmodel/` | Business logic, state, Provider ChangeNotifier |
| `model/` | Data classes, DTOs |
| `service/` | API calls, local storage, external integrations |

---

## Never

- Put business logic inside widget `build()` methods — belongs in ViewModel
- Call APIs directly from widgets — always via service layer
- Use `setState` in favor of Provider for shared state
- Import packages not declared in `pubspec.yaml`
- Mix platform-specific code without proper `Platform.isAndroid` / `Platform.isIOS` guards
