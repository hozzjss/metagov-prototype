from app import core
from tinydb.database import Document
from .contract import Contract, Pool
import logging

class Account:
    def __init__(self, user):
        self.account_table = core.db.table('accounts')
        self.logger = logging.getLogger(".".join([self.__module__, type(self).__name__]))
        self.id = user.id
        self.user = user

        if not self.in_database():
            self.add_to_database()
    
    def in_database(self):
        return self.account_table.contains(doc_id=self.id)
    
    def add_to_database(self):
        # initializing default account data
        entry = {
            'full_name': self.user.name,
            'screen_name': self.user.screen_name,
            'balance': '0',
            'contracts': []
        }

        # inserting account data into table
        self.account_table.insert(Document(
            entry, 
            doc_id=self.id
        ))

        # updating number of accounts
        def increment_num_accounts(doc):
            num_accounts = int(doc['num_accounts'])
            num_accounts += 1
            doc['num_accounts'] = str(num_accounts)

        self.account_table.update(
            increment_num_accounts, 
            doc_ids=[0]
        )
    
    def change_balance(self, user_id, amount):
        # passed into tiny db update function, adds to balance
        def add_to_balance(doc):
            doc['balance'] = str(int(doc['balance']) + amount)
        
        # updates account balance
        self.account_table.update(
            add_to_balance,
            doc_ids=[user_id]
        )

    # def transfer_balance(self, user_id, amount):
        

    def generate_contract(self, status):
        self.logger.info(f'Generating new contract for {self.user.screen_name} [{self.id}]')

        new_contract = Contract(status)
        total_value = new_contract.generate()

        if total_value == False:
            logger.warn('Exiting invalid contract')
            return

        # calculates taxed amount and amount to pay users based on total value of contract
        to_pay_engine = round(total_value * core.Consts.tax_rate)
        to_pay_user = total_value - to_pay_engine

        # paid out to user and agreement engine
        self.change_balance(core.engine_id, to_pay_engine)
        self.change_balance(self.id, to_pay_user)
        self.logger.info(f'Paid {self.user.screen_name} [{self.id}] {to_pay_user} XSC ({to_pay_engine} withheld)')

    
    def execute_contracts(self, status):
        self.logger.info(f'Executing contracts for {self.user.screen_name} [{self.id}]')

        text = status.full_text 
        arg = text[text.find("+exe"):].split()[1]

        # extracting amount to spend
        try:
            to_spend = int(arg)
        except ValueError:
            return False
        
        executing_on = status.in_reply_to_status_id

        self.logger.info(f'New execution request spending {to_spend} XSC on status #{executing_on}')

        contract_pool = Pool()
        amount_spent = contract_pool.auto_execute_contracts(self.id, executing_on, to_spend)

        self.change_balance(self.id, -amount_spent)

