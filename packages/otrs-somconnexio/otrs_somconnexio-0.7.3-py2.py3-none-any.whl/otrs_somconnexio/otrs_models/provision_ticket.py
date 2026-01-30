# coding: utf-8
from pyotrs.lib import Ticket

from otrs_somconnexio.client import OTRSClient
from otrs_somconnexio.otrs_models.provision_article import ProvisionArticle
from otrs_somconnexio.services.get_ticket_title import GetTicketTitle


class ProvisionTicket:
    def __init__(self, responsible_data):
        self.responsible_data = responsible_data

    def create(self):
        self.otrs_ticket = OTRSClient().create_otrs_process_ticket(
            self._build_ticket(), self._build_article(), self._build_dynamic_fields()
        )

    @property
    def id(self):
        return self.otrs_ticket.id

    @property
    def number(self):
        return self.otrs_ticket.number

    def _build_ticket(self):
        title = self._ticket_title()
        return Ticket(
            {
                "Title": title,
                "Type": self._ticket_type(),
                "QueueID": self._ticket_queue_id(),
                "State": self._ticket_state(),
                "Priority": self._ticket_priority(),
                "CustomerUser": self._customer_id(),
                "CustomerID": self._customer_id(),
                "Service": self._ticket_service(),
                "SLA": self._ticket_SLA(),
                "Responsible": self._responsible_email(),
            }
        )

    def _build_article(self):
        provision_article = ProvisionArticle(
            self.service_data.technology,
            self.service_data.order_id,
            self.service_type(),
        )
        return provision_article.call()

    def _ticket_title(self):
        return GetTicketTitle(
            self.service_data.technology,
            self.service_data.order_id,
            self.service_type(),
        ).build()

    def _ticket_type(self):
        return self.otrs_configuration.type

    def _ticket_queue_id(self):
        return self.otrs_configuration.queue_id

    def _ticket_state(self):
        return self.otrs_configuration.state

    def _ticket_priority(self):
        return self.otrs_configuration.priority

    def _ticket_activity_id(self):
        return self.otrs_configuration.activity_id

    def _ticket_process_id(self):
        return self.otrs_configuration.process_id

    def _ticket_service(self):
        if hasattr(self.otrs_configuration, "service"):
            return self.otrs_configuration.service
        else:
            return False

    def _ticket_SLA(self):
        if hasattr(self.otrs_configuration, "SLA"):
            return self.otrs_configuration.SLA
        else:
            return False

    def _customer_id(self):
        return self.customer_data.id

    def _responsible_email(self):
        if hasattr(self.responsible_data, "email"):
            return self.responsible_data.email
        else:
            return False
