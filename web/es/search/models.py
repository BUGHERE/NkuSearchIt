from django.db import models


class ES(models.Model):
    MessageID = models.CharField(max_length=200)
    Date = models.CharField(max_length=200)
    From = models.CharField(max_length=200)
    To = models.CharField(max_length=200)
    Subject = models.CharField(max_length=200)
    Mime_Version = models.CharField(max_length=200)
    ContentType = models.CharField(max_length=200)
    ContentTransferEncoding = models.CharField(max_length=200)
    XFrom = models.CharField(max_length=200)
    XTo = models.CharField(max_length=200)
    Xcc = models.CharField(max_length=200)
    Xbcc = models.CharField(max_length=200)
    XFolder = models.CharField(max_length=200)
    XOrigin = models.CharField(max_length=200)
    XFileName = models.CharField(max_length=200)
    Body = models.CharField(max_length=200)