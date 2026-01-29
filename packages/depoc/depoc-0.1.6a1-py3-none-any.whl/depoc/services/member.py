from depoc.resources.methods import Create, Retrieve, Update, Delete
from depoc.objects.member import MemberObject


class Member(
    Create[MemberObject],
    Retrieve[MemberObject],
    Update[MemberObject],
    Delete[MemberObject],
):
    obj = MemberObject
    endpoint = 'members'
    label = 'member'
