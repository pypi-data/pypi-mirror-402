from depoc.resources.methods import Retrieve, Finder
from depoc.objects.contact import ContactObject


class Contact(Retrieve[ContactObject], Finder[ContactObject]):
    obj = ContactObject
    endpoint = 'contacts'
