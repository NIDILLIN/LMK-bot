class UserInfo:
    """
    _id: ID in social network,
    _group: User group in school,
    _from: Place that is user from.
    """
    id: int
    course: int
    group: str
    place: str
    social: str

    def __init__(self, 
                id: int, 
                social: str, 
                course: int, 
                group: str, 
                place: str) -> None:
        self.id = id
        self.course = course
        self.group = group
        self.place = place
        self.social = social

    def list(self):
        return [self.place, self.group, self.id, self.social]