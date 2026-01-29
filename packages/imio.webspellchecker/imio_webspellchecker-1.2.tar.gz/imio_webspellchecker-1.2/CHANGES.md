# Changelog


## 1.2 (2026-01-19)

- Use defer `<script>`'s attribute so it doesn't block the whole page in case the service isn't responding.
  [aduchene]

## 1.1 (2025-07-11)

- Fixed installation by renaming the `base` profile to `install-base` so it is
  no more alphabetically before `default`.
  Removed `metadata.xml` from the `install-base` profile.
  [gbastien, aduchene]

## 1.0 (2025-05-27)

- Add new settings to manage webspellchecker.
  [aduchene]


## 1.0b7 (2024-04-15)

- Added helpers to `get` and `set` config registry values.
  [gbastien]
- Use `plone.app.vocabularies.PortalTypes` instead
 `plone.app.vocabularies.UserFriendlyTypes` for `allowed_portal_types` and
 `disallowed_portal_types` config parameters.
  [gbastien]


## 1.0b6 (2024-04-04)

- Use proper type on the script tags.
  [aduchene]

## 1.0b5 (2024-03-29)

- Use unicode for default values.
  [aduchene]


## 1.0b4 (2024-03-28)

- Fix bad bundling (MANIFEST.in).
  [aduchene]


## 1.0b3 (2024-01-12)

- Allow to restrict the webspellchecker usage by portal types.
  [aduchene]
- Allow to restrict the webspellchecker usage by css attributes (class, id, ...)
  [aduchene]


## 1.0b2 (2023-12-01)

- Replace rst by markdown.
  [aduchene]


## 1.0b1 (2023-12-01)

- Refactor the script registration. We don't rely on Plone built-in tools like
  the resources registry (or portal_javascript in P4) due to inappropriate
  handling of a generated JS file.
  [aduchene]
- Add tests and configure the CI.
  [aduchene]


## 1.0a1 (2023-05-26)

- Initial release.
  [aduchene]
