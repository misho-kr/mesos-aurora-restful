
def make_link(name, version, requirement=None):
  python_requirement_library(
    name = name,
    requirements = [
      python_requirement('%s==%s' % (name, version) if requirement is None else requirement)
    ]
  )


COMMONS_VERSION = '0.3.1'

make_link('twitter.common.app', '%s' % COMMONS_VERSION)
make_link('twitter.common.log', '%s' % COMMONS_VERSION)

make_link('tornado', '3.2.1')
