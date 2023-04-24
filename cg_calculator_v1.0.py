#!/usr/bin/env python
# coding: utf-8

# In[1]:


from datetime import datetime
import numpy as np


# In[112]:


class portfolio:
    
    def __init__(self, name):
        self.name = name
        self.costbase = {}
        self.capitalgain = {}
        self.transactions = None
        
    def import_transactions(self, path):
        
        with open(path) as f:
    
            lines = [line.strip().split(',') for line in f]
            lines = [line for line in lines if line[1].startswith("C")]
            lines = [[line[0]]+line[2].split()[0:3]+line[3:5] for line in lines]
            lines_np = np.array(lines)
            lines_np[:, 0] = [datetime.strptime(datestr, '%d/%m/%Y').date() for datestr in lines_np[:,0]]
            self.transactions = lines_np[np.lexsort((lines_np[:,1], lines_np[:,0]))]
                        
    def off_the_market_transfer(self, datestr, code, unit, value, transfer_out=True):
        
        if transfer_out == True:
            omt = np.array([[datestr, 'S', unit, code, '', value]])
            omt[0,0] = datetime.strptime(datestr, '%d/%m/%Y').date()
        else:
            omt = np.array([[datestr, 'B', unit, code, value, '']])
            omt[0,0] = datetime.strptime(datestr, '%d/%m/%Y').date()
            
        self.transactions = np.concatenate((self.transactions, omt), axis=0)
        self.transactions = self.transactions[np.lexsort((self.transactions[:,1], self.transactions[:,0]))]
        
    def corporate_action(self, datestr, code, unit, value, action='B'):
        if action == 'B':
            ca = np.array([[datestr, action, unit, code, value, '']])
            ca[0,0] = datetime.strptime(datestr, '%d/%m/%Y').date()
        else:
            ca = np.array([[datestr, action, unit, code, '', value]])
            ca[0,0] = datetime.strptime(datestr, '%d/%m/%Y').date()

        self.transactions = np.concatenate((self.transactions, ca), axis=0)
        self.transactions = self.transactions[np.lexsort((self.transactions[:,1], self.transactions[:,0]))]
        
    
    
    def calculate_cg(self):
        for line in self.transactions:
            date, action, unit, code, debit, credit = line
            unit = int(unit)
                
            if code == 'WPL':
                code = "WDS"
        
            if code not in self.costbase.keys():
                self.costbase[code] = {'unit':0, 'value':0}
            if code not in self.capitalgain.keys():
                self.capitalgain[code] = []
            
            if action == 'B':
                self.costbase[code]['date'] = date
                self.costbase[code]['unit'] += unit
                value = float(debit)
                self.costbase[code]['value'] += value
                self.costbase[code]['avg_cost'] = self.costbase[code]['value']/self.costbase[code]['unit']
            
            if action == 'S':
                credit = float(credit)
                cg = credit - self.costbase[code]['avg_cost']*unit
                self.capitalgain[code].append([date, cg])
                self.costbase[code]['unit'] -= unit
                self.costbase[code]['value'] -= self.costbase[code]['avg_cost']*unit
                if self.costbase[code]['unit'] == 0:
                    self.costbase[code]['avg_cost'] = 0
                else:    
                    self.costbase[code]['avg_cost'] = self.costbase[code]['value']/self.costbase[code]['unit']
    
    def print_cg(self, financial_year):
        
        print('\n')
        print('capital gain/loss for '+self.name+' in '+str(financial_year)+' financial year')
        print('--------------------')
        
        total_cg = 0
        
        start_date = '01/07/'+str(financial_year-1)
        start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
        end_date = '30/06/'+str(financial_year)
        end_date = datetime.strptime(end_date, '%d/%m/%Y').date()
        
        for code, cgs in self.capitalgain.items():
            cgs_current_fy = [cg for cg in cgs if datetime.strptime(cg[0], '%Y-%m-%d').date() >= start_date and datetime.strptime(cg[0], '%Y-%m-%d').date() <= end_date]
            if cgs_current_fy != []:
                print(code)
                for cg_current_fy in cgs_current_fy:
                    print(cg_current_fy[0], cg_current_fy[1])
                    total_cg += cg_current_fy[1]
                    
        print('--------------------')
        print('total capital gain/loss:', total_cg)
    
    def save_cg(self, financial_year, destination_path):

        cg_list = []
        
        start_date = '01/07/'+str(financial_year-1)
        start_date = datetime.strptime(start_date, '%d/%m/%Y').date()
        end_date = '30/06/'+str(financial_year)
        end_date = datetime.strptime(end_date, '%d/%m/%Y').date()
        
        for code, cgs in self.capitalgain.items():
            cgs_current_fy = [[cg[0], str(cg[1])] for cg in cgs if datetime.strptime(cg[0], '%Y-%m-%d').date() >= start_date and datetime.strptime(cg[0], '%Y-%m-%d').date() <= end_date]
            if cgs_current_fy != []:
                cgs_current_fy = [[code]+cg_current_fy for cg_current_fy in cgs_current_fy]
                cgs_current_fy = [','.join(cg_current_fy) for cg_current_fy in cgs_current_fy]
                cg_list += cgs_current_fy
        
        with open(destination_path, 'w') as f:
            f.write('\n'.join(cg_list)) 
        


# In[116]:


if __name__ == "__main__":

    path = 'commsec_individual_Transactions.csv'
    individual_p = portfolio('Personal Portfolio')
    individual_p.import_transactions(path)

    #add omt
    date1, code1, unit1, value1 = '05/12/2022', 'PLS', 20362, 93869.82
    date2, code2, unit2, value2 = '05/12/2022', 'SYI', 13182, 373050.6

    individual_p.off_the_market_transfer(date1, code1, unit1, value1)
    individual_p.off_the_market_transfer(date2, code2, unit2, value2)

    # add ca
    datestr, code, unit, value, action = '01/06/2022', 'WDS', 301, 8957.76, 'B'
    individual_p.corporate_action(datestr, code, unit, value, action)

    individual_p.calculate_cg()

    financial_year = 2023
    individual_p.print_cg(financial_year)

    destination_path1 = 'individual_p.csv'
    individual_p.save_cg(financial_year, destination_path1)


    # path2 = 'commsec_trust_Transactions.csv'
    # trust_p = portfolio('Trust Portfolio')
    # trust_p.import_transactions(path2)

    # date1, code1, unit1, value1, transfer_out = '05/12/2022', 'PLS', 20362, 93869.82, False
    # date2, code2, unit2, value2, transfer_out = '05/12/2022', 'SYI', 13182, 373050.6, False


    # trust_p.off_the_market_transfer(date1, code1, unit1, value1, transfer_out)
    # trust_p.off_the_market_transfer(date2, code2, unit2, value2, transfer_out)

    # trust_p.calculate_cg()

    # financial_year = 2023
    # trust_p.print_cg(financial_year)

