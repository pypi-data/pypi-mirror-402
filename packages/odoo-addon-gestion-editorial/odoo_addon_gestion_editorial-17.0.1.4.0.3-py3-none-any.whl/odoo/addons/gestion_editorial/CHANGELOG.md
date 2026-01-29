# Changelog

All notable changes to this Odoo module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fix bug with liquidations and ddaa creation

### Changed

- Remove consignment configuration (by default is False)
- Hide create invoice buttons in deposit return views
- Block creation of invoices from deposit returns views
- Translate some liquidation messages :warning: User action needed: reload spanish and catalan translations.

## [17.0.1.4.0] - 2026-01-16

### Added

- Add setting to install subscriptions module.

### Changed

- Fix bug with getting pricelist in liquidations by linking stock.picking with sale.order and sale.order.line with stock.move when creating a liquidation.
- Change some texts in purchase liq views :warning: User action needed: reload spanish and catalan translations.

### Fixed

- Fix purchase liq status "To invoice" when invoice already exists

## [17.0.1.3.0] - 2026-01-08

### Changed
- Add catalan translation for "Orders" menu title. :warning: User action needed: reload catalan translations.
- Change purchase order translation "Confirmar pedido" to "Confirmar :warning: User action needed: reload spanish translations.
- Set "no" invoice status after confirm to return of sales deposit
- Change message after make a purchase deposit return in related purchase orders
- Change visible columns in liquidation wizard

## [17.0.1.2.4] - 2025-12-17

### Added

- New filters to stock picking view
- New wizard for managing negative ddaa_orders. When closing a negative ddaa_order you can now decide to open a new ddaa_order and distribute the amounts in the new order lines.

### Changed

- Display barcode column only if any row as a barcode (in report views)
- Refactor of editorial liquidations

### Fixed

- Fix error creating product with contact

## [17.0.1.2.3] - 2025-12-04

The last undocumented release. We will document the following versions.
