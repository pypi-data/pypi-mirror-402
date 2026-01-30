# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Employee Document Mixin",
    "version": "14.0.4.2.0",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia, OpenSynergy Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_hr_employee",
        "ssi_transaction_mixin",
        "ssi_decorator",
    ],
    "data": [
        "templates/employee_document_templates.xml",
    ],
}
