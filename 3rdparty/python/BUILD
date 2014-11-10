
def make_link(name, version, requirement=None):
  python_requirement_library(
    name = name,
    requirements = [
      python_requirement('%s==%s' % (name, version) if requirement is None else requirement)
    ]
  )

make_link('tornado', '3.2.1')
