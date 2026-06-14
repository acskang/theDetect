# MDetect Color/Product ObjectClass Check

## Check Time

```text
2026-06-13 20:54:52 KST
```

## Scope

This Step 13 check only inspected the current ObjectClass state and documented the result.

No ObjectClass records were created, modified, or deleted.
No DB schema, migration, server API, Android code, Dataset Build, training, or deployment behavior was changed.

## Current ObjectClass List

| name | display_name | description | color | is_active | sort_order |
| --- | --- | --- | --- | --- | --- |
| `class_01` | `soap_case_pink` | `1. soap case pink` | `#ed333b` | `True` | `10` |
| `class_02` | `soap_case_white` | `2. soap case white` | `#ffffff` | `True` | `20` |
| `class_03` | `soap_case_mint` | `3. soap case mint` | `#8ff0a4` | `True` | `30` |
| `class_04` | `shampoo_case_white` | `4. shampoo case round` | `#f6f5f4` | `True` | `40` |
| `other` | `other` | `Negative or non-target object class for reducing false positives.` | `#f97316` | `True` | `50` |

## Required Class List

```text
soap_case_pink
soap_case_white
soap_case_mint
shampoo_case_white
other
```

## Existing Required Classes

Exact `name` match:

```text
other
```

Display-name match only:

```text
soap_case_pink     currently exists as name=class_01, display_name=soap_case_pink
soap_case_white    currently exists as name=class_02, display_name=soap_case_white
soap_case_mint     currently exists as name=class_03, display_name=soap_case_mint
shampoo_case_white currently exists as name=class_04, display_name=shampoo_case_white
```

Important:

```text
For color/product class training, the recommended model class name is the ObjectClass name itself.
The current class_01/class_02/class_03/class_04 records have matching display_name values, but their name values do not exactly match the required target class names.
```

## Missing Required Classes

Exact `name` match missing:

```text
soap_case_pink
soap_case_white
soap_case_mint
shampoo_case_white
```

## Manual Creation Method From Web Screen

If the administrator decides to create the missing exact-name classes manually:

1. Open the server in a browser.
2. Click `Object Classes` in the left menu.
3. Click `Create class`.
4. Enter `Name`.
5. Enter `Display name`.
6. Enter `Description`.
7. Enter `Color`.
8. Check `Is active`.
9. Enter `Sort order`.
10. Click `Save`.

Do not delete or modify existing classes automatically.
If existing `class_01`~`class_04` records already have labels or dataset history, changing them can affect interpretation of historical labels and trained models. Any cleanup or migration of old class records must be handled as a separate explicit operation.

## Recommended Input Examples

| Name | Display name | Description | Color | Is active | Sort order |
| --- | --- | --- | --- | --- | --- |
| `soap_case_pink` | `soap_case_pink` | `분홍색 비누 케이스` | `#f4a7c5` | checked | `10` |
| `soap_case_white` | `soap_case_white` | `흰색 비누 케이스` | `#e5e7eb` | checked | `20` |
| `soap_case_mint` | `soap_case_mint` | `민트색/연하늘색 계열 비누 케이스` | `#a7f3d0` | checked | `30` |
| `shampoo_case_white` | `shampoo_case_white` | `흰색 샴푸 케이스` | `#f8fafc` | checked | `40` |
| `other` | `other` | `위 4개 객체가 아닌 기타 객체` | `#9ca3af` | checked | `90` |

## Current Recommendation

The administrator should decide one of the following before uploading new training data:

1. Create the four missing exact-name classes manually and use those for new color/product training.
2. Or explicitly keep the existing `class_01`~`class_04` records and accept that the model class names are not the recommended exact names.

For the Step 12 policy, option 1 is cleaner because the model class names become:

```text
soap_case_pink
soap_case_white
soap_case_mint
shampoo_case_white
other
```

## Next Step

After the administrator confirms or manually creates the exact classes:

```text
Upload class-specific images from Image Dataset.
Then label Bounding Boxes in Labeling Workspace using the intended class names.
```
