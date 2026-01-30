from enum import Enum


class GeometrySubjects(Enum):
  GeometryUploaded = 'geometry:uploaded'
  GeometryParsed = 'geometry:parsed'
  GeometryRemoved = 'geometry:removed'


# class GeometryUploaded(Event):
#   sub

# GeometryUploaded = Event()
# GeometryUploaded.subject = GeometrySubjects.GeometryUploaded
# GeometryUploaded.data