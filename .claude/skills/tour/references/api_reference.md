# Driver.js API Reference

## Install

```bash
npm install driver.js
```

## Import

```ts
import { driver } from 'driver.js'
import 'driver.js/dist/driver.css'
```

## driver() Config Options

| Option | Type | Default |
|--------|------|---------|
| `steps` | `DriveStep[]` | — |
| `animate` | `boolean` | `true` |
| `duration` | `number` | `400` |
| `overlayColor` | `string` | `'black'` |
| `overlayOpacity` | `number` | `0.5` |
| `overlayClickBehavior` | `'close' \| 'nextStep' \| fn` | `'close'` |
| `smoothScroll` | `boolean` | `false` |
| `allowClose` | `boolean` | `true` |
| `allowKeyboardControl` | `boolean` | `true` |
| `disableActiveInteraction` | `boolean` | `false` |
| `stagePadding` | `number` | `10` |
| `stageRadius` | `number` | `5` |
| `popoverClass` | `string` | — |
| `popoverOffset` | `number` | `10` |
| `showButtons` | `AllowedButtons[]` | varies |
| `disableButtons` | `AllowedButtons[]` | — |
| `showProgress` | `boolean` | `false` |
| `progressText` | `string` | `'{{current}} of {{total}}'` |
| `nextBtnText` | `string` | — |
| `prevBtnText` | `string` | — |
| `doneBtnText` | `string` | — |

### Hooks (driver-level)

`onHighlightStarted`, `onHighlighted`, `onDeselected`, `onDestroyStarted`, `onDestroyed`, `onNextClick`, `onPrevClick`, `onCloseClick`, `onDoneClick`, `onPopoverRender`

## DriveStep Fields

| Field | Type |
|-------|------|
| `element` | `Element \| string \| (() => Element)` |
| `popover` | `Popover` |
| `disableActiveInteraction` | `boolean` |
| `data` | `Record<string, any>` |
| `onHighlightStarted` | `fn` |
| `onHighlighted` | `fn` |
| `onDeselected` | `fn` |

## Popover Fields

| Field | Type | Default |
|-------|------|---------|
| `title` | `string` | — |
| `description` | `string` | — |
| `side` | `'top' \| 'right' \| 'bottom' \| 'left'` | `'bottom'` |
| `align` | `'start' \| 'center' \| 'end'` | `'start'` |
| `showButtons` | `AllowedButtons[]` | — |
| `disableButtons` | `AllowedButtons[]` | — |
| `nextBtnText` | `string` | — |
| `prevBtnText` | `string` | — |
| `doneBtnText` | `string` | — |
| `showProgress` | `boolean` | `false` |
| `progressText` | `string` | `'{{current}} of {{total}}'` |
| `popoverClass` | `string` | — |
| `onPopoverRender` | `fn` | — |
| `onNextClick` | `fn` | — |
| `onPrevClick` | `fn` | — |
| `onCloseClick` | `fn` | — |
| `onDoneClick` | `fn` | — |

## Instance Methods

```ts
driverObj.drive()          // start tour from step 0
driverObj.drive(2)         // start from step index
driverObj.highlight({...}) // highlight single element
driverObj.moveNext()
driverObj.movePrevious()
driverObj.moveTo(index)
driverObj.getActiveStep()  // DriveStep | undefined
driverObj.getActiveIndex() // number | undefined
driverObj.isActive()       // boolean
driverObj.refresh()        // reposition popover
driverObj.destroy()        // end tour, remove overlay
```
