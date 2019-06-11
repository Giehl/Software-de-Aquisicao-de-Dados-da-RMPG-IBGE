#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Declarar bibliotecas---------------------------------------------------------------------------------------------------

from zipfile import ZipFile
from urllib.request import urlopen,HTTPError
from dateutil.rrule import rrule, DAILY
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import os.path
import wx.adv
import wx
import io

#Abrir a interface----------------------------------------------------------------------------------------------------------

class Interface(wx.Frame):

    def __init__(self,parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, "Aquisição_de_Dados_da_RMPG/IBGE",size=(800,550))

        #Inserir texto na interface---------------------------------------------------------------------------------------

        wx.StaticText(self, 1, 'Data Inicial', (160,80))
        wx.StaticText(self, 1, 'Data Final', (540,80))
        wx.StaticText(self, 1, 'Universidade Federal do Paraná', (260,5))
        wx.StaticText(self, 1, 'Programa de Pós-graduação em Ciências Geodésicas', (200,25))
        wx.StaticText(self, 1, 'Laboratório de Referenciais Geodésicos e Altimetria por Satélites (LARAS)', (150,45))
        
        #Inserir o botão "Extrair" -----------------------------------------------------------------------------------------

        compute = wx.Button(self, label="Extrair",size=(120,45),pos=(600,450))
        compute.Bind(wx.EVT_BUTTON, self.OnCompute)

        #Inserir o botão "Fechar"--------------------------------------------------------------------------------------------
        
        close = wx.Button(self, label="Fechar",size=(120,45),pos=(450,450))
        close.Bind(wx.EVT_BUTTON, self.OnClose)

        #Inserir uma caixa de listagem de seleção múltipla--------------------------------------------------------------------

        sampleList = ['Fortaleza', 'Imbituba', 'Macaé (inativo desde 2015)', 'Salvador', 'Santana', 'Arraial do Cabo']
        self.ma=wx.ComboBox(self, -1, "Escolha um Marégrafo",(70, 400),(200, 30),sampleList, wx.CB_DROPDOWN)

        
        #Inserir o botão "Selecionar" e uma lacauna para inserir a data inicial--------------------------------------------------

        self.Selected1 = wx.TextCtrl(self, -1,"Selecione Data Inicial",size=(150,25),pos=(160,315))
        self.Button1 = wx.Button(self, label="Selecionar",size=(100,35),pos=(50,310))
        self.Button1.Bind(wx.EVT_BUTTON, self.show1)
        
        #Inserir o botão "Selecionar" e um lacauna para inserir a data final-----------------------------------------------------

        self.Selected2 =wx.TextCtrl(self, -1,"Selecione Data Final",size=(150,25),pos=(540,315))
        self.Button2 = wx.Button(self, label="Selecionar",size=(100,35),pos=(430,310))
        self.Button2.Bind(wx.EVT_BUTTON, self.show2)

        #Inserir os calendários ------------------------------------------------------------------------------------------------
        
        self.cal1 = wx.adv.CalendarCtrl(self, 10, wx.DateTime.Now(),size=(300,200),pos=(50,100))
        self.cal1.Bind(wx.adv.EVT_CALENDAR, self.show1)
        
        self.cal2 = wx.adv.CalendarCtrl(self, 10, wx.DateTime.Now(),size=(300,200),pos=(430,100))
        self.cal2.Bind(wx.adv.EVT_CALENDAR, self.show2)
              
    def show1(self,event):
        c1=self.cal1.GetDate()          
        date1=(c1.Format("%d-%m-%Y"))
        self.Selected1.SetValue(str(date1))
        
    def show2(self,event):
        c2=self.cal2.GetDate()
        date2=(c2.Format("%d-%m-%Y"))
        self.Selected2.SetValue(str(date2))
    
    #Extrair os dados da internet e realizar o controle de qualidade-------------------------------------------------------

    def OnCompute(self, event):
        
        #Tornar a variável text global-------------------------------------------------------------------------------------
        
        global text
        
        #Chamar as variáveis escolhidas na interface pelo usuário --------------------------------------------------------
        
        mar = self.ma.GetValue()
        di=self.Selected1.GetValue()
        df=self.Selected2.GetValue()
        
       #Informar uma mensagem de erro------------------------------------------------------------------------------------
     
        if di=="Selecione Data Inicial":
            wx.StaticText(self, 1, "Atenção: Selecione Data Inicial", (100,480))
            return(self)
        elif df=="Selecione Data Final":
            wx.StaticText(self, 1,"Atenção: Selecione Data Final", (100,480))
            return(self)      
      
        #Transformar o formato de data escolhido na interface para dia-mês-ano--------------------------------------------
       
        a=datetime.strptime(di, "%d-%m-%Y").date() - timedelta(days=1)
        b=datetime.strptime(df, "%d-%m-%Y").date() + timedelta(days=1)
        
        if (b>a)==True:
            a=a
            b=b
            
        #Informar uma mensagem de erro------------------------------------------------------------------------------------
        
        else:
            wx.StaticText(self, 1, 'Atenção: Data Final < Data Inicial', (100,480))
            return(self)
       
        #Selecionar as três primeiras letras do nome dos marégrafos para associar ao link---------------------------------

        if mar=="Fortaleza":            
            lk="FOR"
        elif mar=="Imbituba":
            lk="IMB"
        elif mar=="Macae (desativo)":
            lk="MAC"
        elif mar=="Salvador":
            lk="SAL"
        elif mar=="Santana":
            lk="SAN"
        elif mar=="Arraial do Cabo":
            lk="ARC"
        
        #Informar uma mensagem de erro------------------------------------------------------------------------------------
        
        else:
            wx.StaticText(self, 1, 'Atenção: Selecione um Marégrafo', (100,480))
            return(self)
           
        #Extrair e descompactar os dados maregraficos do site do IBGE-------------------------------------------------------
        
        mar=str(mar)  
        dia=hora=valor=dma=[]
        
        for dt in rrule(DAILY, dtstart=a, until=b):
            ymd=dt.strftime("%y%m%d")
            md=dt.strftime("%d%m")
            dmy=dt.strftime("%d/%m/%Y")
            dma=np.append(dma,[dmy])
            link=('https://geoftp.ibge.gov.br/informacoes_sobre_posicionamento_geodesico/rmpg/dados/%s/%s%s.zip' %(md,lk,ymd))
            try:
                url = urlopen(link)
            except HTTPError:
                continue
            zf = ZipFile(io.BytesIO(url.read()))
           
            #Ler e unir os dados de diferetes arquivos--------------------------------------------------------------------
            
            for item in zf.namelist():
                dads=io.BytesIO(zf.read(item))
                dads = np.genfromtxt(dads, dtype=str)
                dads = np.char.replace(dads, ',', '.') 
                dia=np.append(dia,[dads[:,0]])
                hora=np.append(hora,[dads[:,1]])
                valor=np.append(valor,[dads[:,2]]) 
        dads=np.concatenate([[dia],[hora],[valor]])
        da=np.transpose(dads)
        
    #Matriz confeccionada ideal-------------------------------------------------------------------------------------------
    
        dma=dma[:len(dma)-1]
        dma=dma[1:]
        MC=datenum=[]
        for f in range (0,len(dma),1):
            for hor in range(0,24,1):    
                for minu in range(0,56,5):   
                    F='%s#%.2d:%.2d:00' %(dma[f],hor,minu)
                    MC=np.append(MC,F)
                    datt='%s %.2d:%.2d:00' %(dma[f],hor,minu)
                    datt=str(datt)
                    dw = datetime.strptime(datt, "%d/%m/%Y %H:%M:%S")
                    datenum=np.append(datenum,mdates.date2num(dw))
                    datenum=np.transpose(np.array(datenum))
 
    #Mudando o formato----------------------------------------------------------------------------------------------------
    
        d_2=d_3=[]
        for i in range (0,len(da),1):
            q='%s#%s' %(da[i,0],da[i,1])
            d_3=np.append(d_3,da[i,2])
            d_2=np.append(d_2,q)
        drr=np.concatenate([[d_2],[d_3]])
        drr=np.transpose(drr)
        
    #Filtrar dados sobrantes----------------------------------------------------------------------------------------------
    
        drNM=drdata=[]
        for e in range (0,len(MC),1):
            if np.any(drr==MC[e]):
                ldate=np.where(drr==MC[e])
                drrdata=drr[ldate[0],ldate[1]]
                drrNM=drr[ldate[0],ldate[1]+1]
                try:
                    type(float(str(drrNM).strip("'[]'")))==float
                    drrNM=drrNM
                    drrdata=drrdata      
                    drdata=np.append(drdata,drrdata)
                    drNM=np.append(drNM,drrNM)
                except ValueError:
                    continue
            dr=np.concatenate([[drdata],[drNM]])
            dr=np.transpose(dr)
            
    #Tratar os dados faltantes e os dados repetidos------------------------------------------------------------------------
    
        dNM=ddata=dhora=[]
        for mc in range (0,len(MC),1):
            if np.any(dr==MC[mc]):
                wdate=np.where(dr==MC[mc])  
                col3=dr[wdate[0],wdate[1]+1]
            else:
                col3=np.NaN
            col1,col2 = MC[mc].split("#")
            ddata=np.append(ddata,col1)
            dhora=np.append(dhora,col2)
            dNM=np.append(dNM,col3)

    #Preparar os dados para salvar em arquivo de texto-------------------------------------------------------------------
    
        col_data={'Date':ddata,'Time':dhora,'SeeLevel':dNM}
        text= pd.DataFrame(data=col_data)
        pd.set_option('max_rows', len(text))
        text = text[['Date', 'Time','SeeLevel']]
        text=text.to_string(index=False)
    
        self.Destroy()
        self.Salve = Interface2(wx.Frame)
        self.Salve.Show()
        
   #Fechar o programa caso o usuário clicar em "Fechar"----------------------------------------------------------------

    def OnClose(self, event):
        self.Destroy()

#Abrir uma nova interface para salvar o arquivo de texto---------------------------------------------------------------
        
class  Interface2(wx.Frame):
    def __init__(self,parent):
        super(Interface2, self).__init__(None, size=(400,200))
        self.SetTitle('finalizado com sucesso')
        compute = wx.Button(self, label="Salvar como",size=(80,25),pos=(150,150))
        compute.Bind(wx.EVT_BUTTON, self.OnSaveAs)

    def OnSaveAs(self,Interface):
        dialog = wx.FileDialog(self, "Salvar arquivo:", ".", "", "Text (*.txt)|*.txt", wx.FD_SAVE| wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            self.filename = dialog.GetFilename()
            self.dirname = dialog.GetDirectory()
            textfile = open(os.path.join(self.dirname, self.filename), 'w')
            np.savetxt(textfile, np.column_stack(text),delimiter='', fmt='%.4s')
        
        #Fechar o programa------------------------------------------------------------------------------------------------
        
        dialog.Destroy()
        self.Destroy()
       
def main():
    app = wx.App()
    Interface(None).Show()
    app.MainLoop()
if __name__ == '__main__':
    main()