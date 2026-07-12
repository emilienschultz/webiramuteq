# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import urllib.request, urllib.error, urllib.parse #migration de module PY3
import socket

#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
import langue
langue.run()


# utilisé seulement depuis iramuteq.py


def NewVersion(parent):
    version = parent.version.split(' ')
    if len(version) == 3:
        versionnb = float(version[0])
        versionsub = int(version[2])
    else:
        versionnb = float(version[0])
        versionsub = False
    erreur = False
    new = False
    lien = "http://www.iramuteq.org/current_version"
    try:
        LastVersion = urllib.request.urlopen(lien,data=None,timeout=3)
        lastversion = LastVersion.readlines()
        lastversion = lastversion[0].decode('utf8').replace('\n', '').split('-')
        if len(lastversion) == 2 :
            if (float(lastversion[0]) > versionnb) :
                new = True
            elif float(lastversion[0]) == versionnb and versionsub :
                if versionsub < int(lastversion[1].replace('alpha', '')):
                    new = True
        elif len(lastversion) == 1 :
            if (float(lastversion[0]) >= versionnb) and (versionsub) :
                new = True
            elif (float(lastversion[0]) > versionnb) and not versionsub :
                new = True
    except :
        erreur = "la page n'est pas accessible"
        print(erreur)
    if not erreur and new :
        msg = _("""A new release of IRaMuTeQ is out (%s) !
                You can dowload it from iramuteq website :
                http://www.iramuteq.org""") % '-'.join(lastversion)
#        msg = """
#Une nouvelle version d'IRaMuTeQ (%s) est disponible.
#Vous pouvez la télécharger à partir du site web iramuteq :
#http://www.iramuteq.org""" % '-'.join(lastversion)
        dlg = wx.MessageDialog(parent, msg, _("New release is out !"), wx.OK | wx.ICON_WARNING)
        dlg.CenterOnParent()
        if dlg.ShowModal() in [wx.ID_NO, wx.ID_CANCEL]:
             evt.Veto()
