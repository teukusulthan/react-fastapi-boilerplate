# Command: /generate-screen

Generates a complete Flutter screen with ViewModel, Service, and UI layers following MVVM architecture.

> This boilerplate has **no mobile app** (`apps/mobile/` does not exist). Use this command only after a Flutter app has been added. For a **web** page or screen use `/generate-ui` (or `apps/web/AI_GUIDE.md` §5.1 for route + menu) and load the `reactjs-ui-design` skill first.

## Trigger

`/generate-screen [screen_name]`

---

## Execution Steps

1. `<thinking>` Analyze the purpose of `[screen_name]`. Identify required states (idle, loading, success, error), data inputs, and API endpoints.
2. Apply `@mobile-engineer` constraints — Provider + MVVM, no BLoC/Cubit.
3. Generate the **Model** layer — data class with `fromJson`/`toJson`.
4. Generate the **Service** layer — API calls using standard `http` package, returns `Result` or throws typed errors.
5. Generate the **ViewModel** layer — `ChangeNotifier` class with state fields, calls service, notifies listeners.
6. Generate the **View** layer — `StatelessWidget` using `Consumer<ViewModel>`, `Scaffold`, `AppBar`, `Body`. Use `const` widgets where applicable.

---

## Output Format

Map code to MVVM folder structure:

```
lib/features/[screen_name]/
├── models/          ← [ScreenName]Model
├── services/        ← [ScreenName]Service
├── viewmodels/      ← [ScreenName]ViewModel (ChangeNotifier)
└── views/
    ├── [screen_name]_view.dart
    └── widgets/     ← reusable sub-widgets for this screen
```

Ensure responsive layout and accessible UI. All loading/error/empty states must be handled in the View.
