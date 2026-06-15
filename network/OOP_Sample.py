class Ticket:
    def __init__(self, ticket_id, subject, description, date, comments):
        self.ticket_id = ticket_id
        self.subject = subject
        self.description = description
        self.date = date
        self.comments = comments

    def __str__(self):
        return f"Ticket ID: {self.ticket_id}\nSubject: {self.subject}\nDescription: {self.description}\nDate: {self.date}\nComments: {self.comments}"


class Customer:
    def __init__(self, national_id, name, customer_type):
        self.national_id = national_id
        self.name = name
        self.customer_type = customer_type
        self.tickets = {}

    def add_ticket(self, ticket):
        self.tickets[ticket.ticket_id] = ticket

    def get_ticket(self, ticket_id):
        return self.tickets.get(ticket_id)


    # returning an error if someone looks for an attribute of a non-existing ticket
    def __getattr__(self, item):
        if item in self.tickets:
            return self.tickets[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")


def main():
    # Create customers
    cus1 = Customer('12345', 'Alice', 'Premium')
    cus2 = Customer('67890', 'Bob', 'Regular')

    # Create tickets
    ticket1 = Ticket(101, 'Issue with product', 'The product does not work as expected', '2024-08-01', ['Comment1', 'Comment2'])
    ticket2 = Ticket(102, 'Billing problem', 'Incorrect billing amount', '2024-08-02', ['Comment3', 'Comment4'])
    ticket3 = Ticket(103, 'Issue with your mom', 'Your mom does not work as expected', '2024-08-03', ['Comment5', 'Comment6'])
    ticket4 = Ticket(104, 'No problem', 'Just Kidding', '2024-08-04', ['Comment7', 'Comment8'])

    # Add tickets to customers
    cus1.add_ticket(ticket1)
    cus1.add_ticket(ticket2)
    cus1.add_ticket(ticket3)
    cus2.add_ticket(ticket4)

    # Command interface
    while True:
        cmd = input("Enter 'show <customer_id> <ticket_id>' to view ticket details or 'exit' to quit: ")
        if cmd.lower() == 'exit':
            break
        try:
            parts = cmd.split()
            if len(parts) != 3 or parts[0].lower() != 'show':
                raise ValueError("Invalid command format. Use 'show <customer_id> <ticket_id>'.")

            customer_id = parts[1]
            ticket_id = int(parts[2])

            if customer_id == 'cus1':
                customer = cus1
            elif customer_id == 'cus2':
                customer = cus2
            else:
                raise ValueError("Unknown customer ID.")

            ticket = customer.get_ticket(ticket_id)
            if ticket:
                print(ticket)
            else:
                print(f"Ticket ID {ticket_id} not found for customer {customer_id}.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
