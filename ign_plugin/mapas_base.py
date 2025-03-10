# -*- coding: utf-8 -*-
"""
/***************************************************************************
 mapasBase
                                 A QGIS plugin
 Este plugin permite descargar mapas base, archivos wms y wfs del IGN.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-01-23
        git sha              : $Format:%H$
        copyright            : (C) 2023 by IGN
        email                : ign@ign.gob.ar
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
#////////////////////////////////////////////////// LIBRERIAS NECESARIAS /////////////////////////////////////////////////////////#
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem
from qgis.PyQt.QtWidgets import QAction


from qgis.core import ( 
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer 
    )

# Initialize Qt resources from file resources.py
from .resources import *

import os # This is is needed in the pyqgis console also 

# Import the code for the DockWidget
from .mapas_base_dockwidget import mapasBaseDockWidget
import os.path

import qgis.utils ###

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import QBrush, QColor

import json
import webbrowser
import requests


#////////////////////////////////////////////////// CLASE PRINCIPAL /////////////////////////////////////////////////////////#
class mapasBase:
    """QGIS Plugin Implementation."""


#                                       ///////// FUNCIONES /////////
#""" We define the dictionary of layers outside the functions so that it is accessible in all """
    def __init__(self, iface): #Este método se ejecuta cada vez que se inicia el complemento
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'mapasBase_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&IGN Plugin')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'mapasBase')
        self.toolbar.setObjectName(u'mapasBase')


        self.pluginIsActive = False
        self.dockwidget = None


#///////////////////////////////////////////////////////////////////////////////////////////////////////////#     
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('mapasBase', message)


#///////////////////////////////////////////////////////////////////////////////////////////////////////////#
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


#///////////////////////////////////////////////////////////////////////////////////////////////////////////#
    def initGui(self): #se llama automáticamente cuando el usuario abre el plugin. 
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/mapas_base/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'IGN Plugin'), 
            callback=self.run,
            parent=self.iface.mainWindow())


#///////////////////////////////////////////////////////////////////////////////////////////////////////////#
    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING mapasBase"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        self.dockwidget = None 

        self.pluginIsActive = False
        

#///////////////////////////////////////////////////////////////////////////////////////////////////////////#
    def unload(self): #se llama automáticamente cuando el usuario cierra el plugin.
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD mapasBase"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&IGN Plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


####################################### ####################################### #######################################  
    ########################################      INICIO RUN     ###############################################    
####################################### ####################################### ####################################### 
    def run(self):

        """Run method that loads and starts the plugin"""
                #result = self.dockwidget.exec()
        if not self.pluginIsActive:
            self.pluginIsActive = True


         # dockwidget may not exist if:
         #    first run of plugin
         #    removed on close (see self.onClosePlugin method)
            if not self.dockwidget:
            # Create the dockwidget (after translation) and keep reference
                self.dockwidget = mapasBaseDockWidget() #crea la interfaz grafica       

        # connect to provide cleanup on closing of dockwidget   
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

   #....................... LOGO IGN ..........................#
            self.dockwidget.cargarLogo() # para cargar logo por defecto cuando se abre el plugin
  

    #................. VISTA PREVIA DE MAPA BASE .......................#
            self.dockwidget.cargarMapa() #para cargar vista previa de mapa por defecto cuando se abre el plugin
    


    #.............................. Imprimir arbol WMS a partir de json - WEB ..................................#
    #LECTURA JSON A TRAVES DE URL
            url = "https://raw.githubusercontent.com/etengler/complementoQgis_v1/main/wms.json"
            response = requests.get(url)

            if response.status_code == 200:
                content = response.content.decode('utf-8')
                self.capasWMS = json.loads(content)
                self.crearArbolWMS(self.capasWMS)

            else:
                print("Error: No se pudo obtener el contenido del archivo JSON")

        #.............................. Imprimir arbol WFS a partir de json - WEB ..................................#
    #LECTURA JSON A TRAVES DE URL
            url = "https://raw.githubusercontent.com/etengler/complementoQgis_v1/main/wfs.json"
            response = requests.get(url)

            if response.status_code == 200:
                content = response.content.decode('utf-8')
                self.capasWFS = json.loads(content)
                self.crearArbolWFS(self.capasWFS)

            else:
                print("Error: No se pudo obtener el contenido del archivo JSON") 
            

    #...............................  WFS  .................................#
    #esconder el listView al abrir el pluggin (widget que escoonde al arbol y muestra las opciones de capas según la busqueda)
            self.dockwidget.listView_WFS.setVisible(False)
    #esconder boton para cargar capa por buscador
            self.dockwidget.pushButton_WFS2.setVisible(False)
    #inicializa valor de capa seleccionada de buscador WFS(model)
            self.indiceWFS= None
    
    #..............................  WMS  ..................................#
    #esconder el listView al abrir el pluggin (widget que escoonde al arbol y muestra las opciones de capas según la busqueda)
            self.dockwidget.listView_WMS.setVisible(False)
    #esconder boton para cargar capa por buscador
            self.dockwidget.pushButton_WMS2.setVisible(False)
    #inicializa valor de capa seleccionada de buscador WFS(model)
            self.indiceWMS= None


    #................................ SOLAPA MAPA BASE ..................................#
    #-------------------------- BOTON CARGAR MAPA BASE AL PROYECTO ---------------------------------#
            self.dockwidget.pushButton.clicked.connect(self.cargarMapaBase)
   
    #--------------------------  VISTA REVIA AL CLICKEAR MAPA BASE  --------------------------------#     
            self.dockwidget.radioButton_1.clicked.connect(self.dockwidget.cargarMapa)
            self.dockwidget.radioButton_2.clicked.connect(self.dockwidget.cargarMapa)
            self.dockwidget.radioButton_3.clicked.connect(self.dockwidget.cargarMapa)
            self.dockwidget.radioButton_4.clicked.connect(self.dockwidget.cargarMapa)
            self.dockwidget.radioButton_5.clicked.connect(self.dockwidget.cargarMapa)


    #............................... SOLAPA DE DESCARGA - chequear arbol..................................#
            self.dockwidget.pushButton_WFS.clicked.connect(self.chequearArbolWFS) #chequea que capa esta seleccionada al apretar el boton cargar capa y carga la capa wfs
            self.dockwidget.pushButton_WMS.clicked.connect(self.chequearArbolWMS) #chequea que capa esta seleccionada al apretar el boton cargar capa y carga la capa wms


    #................................ SOLAPA DE DESCARGA - buscador wfs ..................................#
    #buscar capas
            self.dockwidget.lineEdit_WFS.textChanged.connect(self.buscarCapaWFS) #llama a la funcion si se edita la linea de texto
    #Cargar capa por buscador WFS
            self.dockwidget.pushButton_WFS2.clicked.connect(self.cargarCapaPorBuscadorWFS) #carga la capa seleccionada por buscador
            self.dockwidget.listView_WFS.clicked[QtCore.QModelIndex].connect(self.obtenerIndiceModelWFS) #se ejecuta cada vez que se cliquea una opcion de la lista. Y se guarda ese valor.
   

    #............................... SOLAPA DE DESCARGA - buscador wms  .................................#
    #buscar capas
            self.dockwidget.lineEdit_WMS.textChanged.connect(self.buscarCapaWMS) #llama a la funcion si se edita la linea de texto
    #Cargar capa por buscador WFS
            self.dockwidget.pushButton_WMS2.clicked.connect(self.cargarCapaPorBuscadorWMS) #carga la capa seleccionada por buscador
            self.dockwidget.listView_WMS.clicked[QtCore.QModelIndex].connect(self.obtenerIndiceModelWMS) #se ejecuta cada vez que se cliquea una opcion de la lista. Y se guarda ese valor.
       

    #............................................   show the dockwidget  ....................................................#
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.NoDockWidgetArea, self.dockwidget) 
            self.dockwidget.show() 


    #...........................................  links  externos  .................................................#
            self.dockwidget.button_link.clicked.connect(self.openLink)
            self.dockwidget.button_link.setToolTip("Ir al visor de mapas ArgenMap")

            self.dockwidget.button_CapasSig.clicked.connect(self.openLink_capasSig)
            self.dockwidget.button_CapasSig.setToolTip("Ir a Capas Sig")

            self.dockwidget.button_Geoservicios.clicked.connect(self.openLink_geoServicios)
            self.dockwidget.button_Geoservicios.setToolTip("Ir a Geoservicios")

    #...........................................  boton cerrar  .................................................#
            self.dockwidget.pushButton_cerrar.clicked.connect(self.onClosePlugin)
            self.dockwidget.pushButton_cerrar_2.clicked.connect(self.onClosePlugin)
            self.dockwidget.pushButton_cerrar_3.clicked.connect(self.onClosePlugin)

####################################### ####################################### ####################################### 
        #######################################      METODOS     ###############################################    
####################################### ####################################### ####################################### 

  #...............................   BUSCADOR  wms y wfs ............................... 
    def buscarCapaWFS(self): # entra a este metodo cada ve que se modifica algun caracter en el buscador        
        self.txt_busca_capa_wfs = self.dockwidget.lineEdit_WFS.text()  #guardo el nuevo texto/caracter en la variable de clase
        print(self.txt_busca_capa_wfs) #imprime lo que esta en el buscador
        
        if len(self.txt_busca_capa_wfs) <1: #si no hay ningun caracter
            #se ve arbol completo
            self.dockwidget.listView_WFS.setVisible(False)
            self.dockwidget.pushButton_WFS2.setVisible(False)#esconder el boton cargar capa para buscador
            self.indiceWFS= None
        
        else: #si son uno o mas caracteres
            self.dockwidget.listView_WFS.setVisible(True) #se activa la vista de lista con las coincidencias
            self.dockwidget.pushButton_WFS2.setVisible(True) #se hace visible el boton cargar capa para buscador
        
            #crear modelo
            self.modelWFS = QStandardItemModel()
            self.dockwidget.listView_WFS.setModel(self.modelWFS)

            #trae lista con las capas coincidentes
            for padres in self.capasWFS: #Chequeo json
                pass
                for hijo in padres['hijos']: 
                    if self.coincidenEnLetrasConsecutivas(self.txt_busca_capa_wfs.lower(), hijo['name'].lower()):  #si coinciden en dos o mas letras
                        self.modelWFS.appendRow(QStandardItem(hijo['name'])) #la agrego a la listView
               


    def buscarCapaWMS(self): # entra a este metodo cada ve que se modifica algun caracter en el buscador       
        self.txt_busca_capa_wms = self.dockwidget.lineEdit_WMS.text()  #guardo el nuevo texto/caracter en la variable de clase
        #print(self.txt_busca_capa_wms) #imprime lo que esta en el buscador

        if len(self.txt_busca_capa_wms) <1: #si no hay ningun caracter
            #se ve arbol completo
            self.dockwidget.listView_WMS.setVisible(False)
            self.dockwidget.pushButton_WMS2.setVisible(False)#esconder el boton cargar capa para buscador
            self.indiceWMS= None
        
        else: #si son uno o mas caracteres
            self.dockwidget.listView_WMS.setVisible(True) #se activa la vista de lista con las coincidencias
            self.dockwidget.pushButton_WMS2.setVisible(True) #se hace visible el boton cargar capa para buscador
        
            #crear modelo
            self.modelWMS = QStandardItemModel() #listview
            self.dockwidget.listView_WMS.setModel(self.modelWMS)

            #trae lista con las capas coincidentes
            for padres in self.capasWMS: #Chequeo json   
                pass
                for hijo in padres['hijos']: 
                    if self.coincidenEnLetrasConsecutivas(self.txt_busca_capa_wms.lower(), hijo['name'].lower()):  #si coinciden en dos o mas letras
                        self.modelWMS.appendRow(QStandardItem(hijo['name'])) #la agrego a la listView



    #............................... CARGAR CAPA SELECCIONADA EN EL BUSCADOR WFS .................................#
    def cargarCapaPorBuscadorWFS(self):
        if self.indiceWFS is None: #si no seleccione nada
            pass
        else:
            #print("--" + self.indiceWFS.text()) #indice de la seleccion

            #recorro json y busco nombre igual
            for padres in self.capasWFS: 
                pass
                for hijo in padres['hijos']:
                    if self.sonIgualesPalabras(self.indiceWFS.text().lower(), hijo['name'].lower()):  #ver modivficar
                        #print("son iguales" + self.indiceWFS.text() + hijo['nombre'])
                        uri=hijo['url']
                        vlayer=QgsVectorLayer(uri, hijo['name'], "WFS") 
                        QgsProject.instance().addMapLayer(vlayer) #agregao capa al proyecto
                        #break
          


    def cargarCapaPorBuscadorWMS(self):
        if self.indiceWMS is None: #si no seleccione nada
            pass
        else:
            #print("--" + self.indiceWMS.text()) #indice de la seleccion

            #recorro json y busco nombre igual 
            for padres in self.capasWMS: 
                pass #?
                for hijo in padres['hijos']:
                    if self.sonIgualesPalabras(self.indiceWMS.text().lower(), hijo['name'].lower()): 
                        #print("son iguales" + self.indiceWMS.text() + hijo['name'])
                        uri=hijo['url']
                        rlayer=QgsRasterLayer(uri,hijo['name'],"WMS") 
                        QgsProject.instance().addMapLayer(rlayer) #agregao capa al proyecto



    #...................................................... VARIOS ................................................................#
    def coincidenEnLetrasConsecutivas(self,palabra1, palabra2): #palabra 1 = lo que va buscando el usuario  2 = palabra a buscar
        return (palabra1 in palabra2) #psi alabra 1 esta en palabra 2? si una esta contenida en otra


    def sonIgualesPalabras(self,palabra1, palabra2): #palabra 1 = lo que va buscando el usuario  2 = palabra a buscar 
        return (palabra1 == palabra2) #si son iguales

    
    #....................................................  ARBOL  ...............................................................#
    def crearArbolWFS(self, datosWFS): #crea arbol a partir de un json  WFS
        for padres in datosWFS:
            parent = QtWidgets.QTreeWidgetItem(self.dockwidget.treeWidget_wfs)
            parent.setText(0, (padres['padre']))
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate) #pone caja checkbox en padre:| Qt.ItemIsTristate
            parent.setForeground(0, QBrush(QColor(0, 0, 0)))  # Texto negro para el padre

            for hijo in padres['hijos']:
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, (hijo['name']))
                child.setText(1, (hijo['url'])) #columna oculta!!!!!!! como agregarla a los datos del arbol? hasta ahora habia sido solo agregado el nombre al arbol. Faltaba el ingreso a la url
                child.setText(2, (hijo['nombre']))#columna oculta!!!!!!! #?
                child.setCheckState(0, Qt.Unchecked)  
                child.setForeground(0, QBrush(QColor(0, 0, 0)))  # Texto negro para el hijo    



    def crearArbolWMS(self, datosWMS): #crea arbol a partir de un json  WMS
        for padres in datosWMS:
            parent = QtWidgets.QTreeWidgetItem(self.dockwidget.treeWidget_wms)
            parent.setText(0, (padres['padre']))
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate) #pone caja checkbox en padre:| Qt.ItemIsTristate

            for hijo in padres['hijos']:
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, (hijo['name']))
                child.setText(1, (hijo['url'])) #columna oculta!!!!!!! como agregarla a los datos del arbol? hasta ahora habia sido solo agregado el nombre al arbol. Faltaba el ingreso a la url
                child.setText(2, (hijo['nombre']))#columna oculta!!!!!!! 
                child.setCheckState(0, Qt.Unchecked) 



    #................................................ chequear chekbox del arbol ................................................#
    def chequearArbolWFS(self): #ve que checkbox estan seleccionados y los carga al proyecto
        self.treeWFS = self.dockwidget.treeWidget_wfs #guarda en la variable el arbol creado en la funcion creararbol()
        iterator = QTreeWidgetItemIterator(self.treeWFS) #guarda en la variable el iterdaor que seria el primer nodo independientemente de si es padre o hijo...
        #contador=0

        while iterator.value():
            item = iterator.value() #guardo el valor del nodo
            
            if item.parent() is None: #si NO tiene un padre
                pass
                # VER - si esta clickeado es porque todas las capas de la categoria estan seleccionadas
            
            else:   #si TIENE un padre
                 if item.checkState(0): #si esta clickeado  parametros=columna
                    #print(item.text(1))
                    uri=item.text(1) #guarda la url
                    vlayer=QgsVectorLayer(uri, item.text(0), "WFS")  
                    QgsProject.instance().addMapLayer(vlayer) #carga al proyecto todas las capas tildadas
                 
            iterator+=1 



    def chequearArbolWMS(self): #ve que checkbox estan seleccionados y los carga al proyecto
        self.treeWMS = self.dockwidget.treeWidget_wms #guarda en la variable el arbol creado en la funcion creararbol()
        iterator = QTreeWidgetItemIterator(self.treeWMS) #guarda en la variable el iterdaor que seria el primer nodo independientemente de si es padre o hijo...
        
        while iterator.value():
            item = iterator.value() #guardo el valor del nodo
            
            if item.parent() is None: #si NO tiene un padre
                pass
                # VER - si esta clickeado es porque todas las capas de la categoria estan seleccionadas
            
            else:   #si TIENE un padre
                 if item.checkState(0): #si esta clickeado  parametros=columna
                    uri=item.text(1) #guarda la url
                    rlayer=QgsRasterLayer(uri,item.text(0),"WMS") 
                    QgsProject.instance().addMapLayer(rlayer) #carga al proyecto todas las capas tildadas
                 
            iterator+=1 


#............................................................................................#
    def obtenerIndiceModelWFS(self, index):  #obtiene el indice de la capa seleccionada en cada momento
        self.indiceWFS = self.modelWFS.itemFromIndex(index) #se debe borrar en alguna parte
        #print("la capa seleccionada en este momento es: " + self.indiceWFS.text())
        

    def obtenerIndiceModelWMS(self, index):  #obtiene el indice de la capa seleccionada en cada momento
        self.indiceWMS = self.modelWMS.itemFromIndex(index) #se debe borrar en alguna parte
        #print("la capa seleccionada en este momento es: " + self.indiceWFS.text())
        


#-------------------------------- cargar mapa base -----------------------------------------# 
    def cargarMapaBase(self): #cargar mapa base cuando se cliquea boton "cargar mapa base", segun seleccion
        #valor= self.dockwidget.comprobarRadioButton() #trae valor segun que radio button este apretado
        if self.dockwidget.radioButton_1.isChecked():
            self.cargarArgenMap()
        if self.dockwidget.radioButton_2.isChecked():
            self.cargarArgenMapGris()
        if self.dockwidget.radioButton_3.isChecked():
            self.cargarTopografico()
        if self.dockwidget.radioButton_4.isChecked():
            self.cargarOscuro()
        if self.dockwidget.radioButton_5.isChecked():
            self.cargarHibrido()    


#------------------------------------ links externos --------------------------------------------#
    def openLink(self): #ir al visor de mapas argenmap
        #falta si funciona el link...
        url = "https://mapa.ign.gob.ar/?zoom=4&lat=-40&lng=-59&layers=argenmap"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Esto generará una excepción si el código de estado no es 2xx
            webbrowser.open(url)
        except requests.exceptions.RequestException as e:
            self.dockwidget.button_link.setToolTip("No funciona el servicio ArgenMap")
            print("Error al acceder a la URL:", e)


    def openLink_capasSig(self): #ir al visor de mapas argenmap
        #falta si funciona el link...
        url = "https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/CapasSIG"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Esto generará una excepción si el código de estado no es 2xx
            webbrowser.open(url)
        except requests.exceptions.RequestException as e:
            self.dockwidget.button_link.setToolTip("No funciona el servicio de Capas SIG")
            print("Error al acceder a la URL:", e)
            

    
    def openLink_geoServicios(self): #ir al visor de mapas argenmap
        #falta si funciona el link...
        url = "https://www.ign.gob.ar/NuestrasActividades/InformacionGeoespacial/ServiciosOGC"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Esto generará una excepción si el código de estado no es 2xx
            webbrowser.open(url)
        except requests.exceptions.RequestException as e:
            self.dockwidget.button_link.setToolTip("No funciona el Geoservicio del IGN")
            print("Error al acceder a la URL:", e)




    ################################################   MAPAS BASE IGN    ########################################### trae mapa al proyecto
    def cargarArgenMap(self):
        uri="type=xyz&url=https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG%3A3857@png/{z}/{x}/{-y}.png"
        rlayer=QgsRasterLayer(uri,"Argenmap","WMS") 
                
        if not rlayer.isValid(): #siempre es valido...
            print("wms argenmap fallo!") 
        else: 
            QgsProject.instance().addMapLayer(rlayer)
            

    def cargarArgenMapGris(self):
        uri="type=xyz&url=https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/mapabase_gris@EPSG%3A3857@png/{z}/{x}/{-y}.png"

        rlayer=QgsRasterLayer(uri,"Argenmap Gris","WMS") 
                
        if not rlayer.isValid(): 
            print("wms argenmapGris fallo!") 
        else:
            QgsProject.instance().addMapLayer(rlayer)   


    def cargarTopografico(self):
        uri="type=xyz&url=https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/mapabase_topo@EPSG%3A3857@png/{z}/{x}/{-y}.png"
        rlayer=QgsRasterLayer(uri,"Argenmap Topografico","WMS") 
                
        if not rlayer.isValid(): 
            print("wms topografico fallo!") 
        else:
            QgsProject.instance().addMapLayer(rlayer)


    def cargarOscuro(self):
        uri="type=xyz&url=https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/argenmap_oscuro@EPSG%3A3857@png/{z}/{x}/{-y}.png"
        rlayer=QgsRasterLayer(uri,"Argenmap Oscuro","WMS") 
                
        if not rlayer.isValid(): 
            print("wms oscuro fallo!") 
        else:
            QgsProject.instance().addMapLayer(rlayer)

    def cargarHibrido(self):
        uri="type=xyz&url=https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/mapabase_hibrido@EPSG%3A3857@png/{z}/{x}/{-y}.png" #hibrido
        rlayer=QgsRasterLayer(uri,"Argenmap Híbrido","WMS") 

        uri_esri="type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D" #hibrido
        rlayer_esri=QgsRasterLayer(uri_esri,"ESRI Satellite","WMS") 

                
        if not rlayer.isValid(): 
            print("wms híbrido fallo!") 
        else:
            QgsProject.instance().addMapLayer(rlayer_esri)
            QgsProject.instance().addMapLayer(rlayer)
            
            #https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/mapabase_hibrido@EPSG%3A3857@png/{z}/{x}/{-y}.png
            #https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D

    

