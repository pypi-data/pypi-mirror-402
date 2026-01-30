# coding: utf-8
import unittest
from mock import Mock, patch

from otrs_somconnexio.otrs_models.switchboard_ticket import SwitchboardTicket
from otrs_somconnexio.otrs_models.configurations.provision.switchboard_ticket import (
    SwitchboardTicketConfiguration,
)


class SwitchboardTicketTestCase(unittest.TestCase):
    def setUp(self):
        self.responsible_data = Mock(spec=["email"])
        self.service_data = Mock(
            spec=["order_id", "technology", "landline", "mobile_phone_number"]
        )
        self.service_data.order_id = 123
        self.customer_data = Mock(spec=["id"])

    @patch("otrs_somconnexio.otrs_models.provision_ticket.Ticket")
    def test_build_ticket(self, MockTicket):
        self.service_data.landline = False
        self.service_data.mobile_phone_number = False

        expected_ticket_arguments = {
            "Title": "Provisió centraleta virtual (CV)",
            "Type": SwitchboardTicketConfiguration.type,
            "QueueID": SwitchboardTicketConfiguration.queue_id,
            "State": SwitchboardTicketConfiguration.state,
            "SLA": "No pendent resposta",
            "Service": "Centraleta Virtual",
            "Priority": SwitchboardTicketConfiguration.priority,
            "CustomerUser": self.customer_data.id,
            "CustomerID": self.customer_data.id,
            "Responsible": self.responsible_data.email,
        }

        SwitchboardTicket(
            self.service_data, self.customer_data, self.responsible_data
        )._build_ticket()
        MockTicket.assert_called_with(expected_ticket_arguments)

    def test_title_with_landline(self):
        self.service_data.landline = "999999999"
        ticket = SwitchboardTicket(
            self.service_data, self.customer_data, self.responsible_data
        )
        self.assertEqual(ticket._ticket_title(), "Alta número de fix (CV)")

    def test_title_with_mobile_phone_number(self):
        self.service_data.landline = None
        self.service_data.mobile_phone_number = "699999999"
        ticket = SwitchboardTicket(
            self.service_data, self.customer_data, self.responsible_data
        )
        self.assertEqual(ticket._ticket_title(), "Alta mòbil agent (CV)")

    @patch("otrs_somconnexio.otrs_models.provision_ticket.ProvisionArticle")
    def test_build_article(self, MockProvisionArticle):
        mock_article = MockProvisionArticle.return_value

        SwitchboardTicket(
            self.service_data, self.customer_data, self.responsible_data
        )._build_article()
        MockProvisionArticle.assert_called_with(
            self.service_data.technology,
            self.service_data.order_id,
            "switchboard",
        )
        mock_article.call.assert_called_once()

    @patch("otrs_somconnexio.otrs_models.switchboard_ticket.SwitchboardDynamicFields")
    def test_build_dynamic_fields(self, MockSwitchboardDynamicFields):
        mock_dyn_fields = MockSwitchboardDynamicFields.return_value

        SwitchboardTicket(
            self.service_data, self.customer_data, self.responsible_data
        )._build_dynamic_fields()
        MockSwitchboardDynamicFields.assert_called_with(
            self.service_data,
            self.customer_data,
            SwitchboardTicketConfiguration.process_id,
            SwitchboardTicketConfiguration.activity_id,
        )
        mock_dyn_fields.all.assert_called_once()

    @patch("otrs_somconnexio.otrs_models.provision_ticket.OTRSClient")
    def test_create(self, MockOTRSClient):
        service_data = Mock(
            spec=[
                "order_id",
                "iban",
                "email",
                "contact_phone",
                "product",
                "technology",
                "sales_team",
                "type",
                "landline",
                "mobile_phone_number",
                "icc",
                "has_sim",
                "extension",
                "agent_name",
                "agent_email",
                "previous_owner_vat",
                "previous_owner_name",
                "previous_owner_surname",
                "shipment_address",
                "shipment_city",
                "shipment_zip",
                "shipment_subdivision",
                "additional_products",
                "activation_notes",
                "notes",
                "confirmed_documentation",
            ]
        )
        customer_data = Mock(
            spec=[
                "id",
                "first_name",
                "name",
                "vat_number",
                "street",
                "city",
                "zip",
                "subdivision",
                "has_active_contracts",
                "language",
            ]
        )

        mock_otrs_client = Mock(spec=["create_otrs_process_ticket"])
        mock_otrs_client.create_otrs_process_ticket.return_value = Mock(
            SwitchboardTicket, autospec=True
        )
        mock_otrs_client.create_otrs_process_ticket.return_value.id = 123
        mock_otrs_client.create_otrs_process_ticket.return_value.number = "#123"
        MockOTRSClient.return_value = mock_otrs_client

        ticket = SwitchboardTicket(service_data, customer_data, self.responsible_data)
        ticket.create()

        mock_otrs_client.create_otrs_process_ticket.assert_called_once()
        self.assertEqual(ticket.id, 123)
        self.assertEqual(ticket.number, "#123")
