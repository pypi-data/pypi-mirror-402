from importlib import import_module
from inspect import getmodule
from pathlib import Path
from re import match


class ClassFamily:

    # Return an attribute of this specific class, not inherited.

    @classmethod
    def get_member_attr(self, attribute):
        if attribute in self.__dict__:
            return self.__dict__[attribute]

    # True or False: This class has all the attributes provided. Return True if
    # no attributes provided. Use __subclasses__ so we only look at direct
    # descendents, and __dict__ so we only look at attributes defined here (not
    # inherited).

    @classmethod
    def has_member_attrs(self, *attributes):

        # Do I have all the attributes?
        matches = [a in self.__dict__ for a in attributes]

        # Python's all() function returns True if the list is empty. So we kill
        # two birds with one stone here - get a hit if there are no attributes,
        # and avoid the empty-matches problem.
        return all(matches + list(attributes))

    # Return a set of myself and all my descendents that have certain
    # attributes. If no attribute names are provided, return the entire family.

    @classmethod
    def family_members(self, *attributes):

        # Put myself into a set if I qualify
        hits = {self} if self.has_member_attrs(*attributes) else set()

        # Go through my subclasses
        for kid in self.family_children():

            # Call the same function on each subclass
            hits |= kid.family_members(*attributes)

        # Send it back
        return hits

    @classmethod
    def family_attrs(self, attribute):  # pragma: nocover
        """
        Return a set of all the values of a specific attribute that exist in
        the family. The set avoids repetition of values in the result. This is
        a legacy method, not currently tested or used.
        """
        # Put myself into a set if I qualify
        if self.has_member_attrs(attribute):
            values = {self.get_member_attr(attribute)}
        else:
            values = set()

        # Go through my subclasses
        for kid in self.family_children():

            # Call the same function on each subclass
            values |= kid.family_attrs(attribute)

        # Send it back
        return values

    @classmethod
    def family_member(self, attribute, value):
        """Return a specific family member that has a specified value of an
        attribute. Assume that there is only one, so return it as soon as it's
        found."""

        # See if I qualify, and if so, return myself. Use __dict__ rather than
        # hasattr() and getattr() to refer only to myself, rather than
        # inherited attributes.
        if attribute in self.__dict__:
            if self.__dict__[attribute] == value:
                return self

        # Go through the subclasses, doing the same. The return statement will
        # exit the loop, so we get out as soon as we find one, without having
        # to evaluate others.
        for kid in self.family_children():
            found = kid.family_member(attribute, value)
            if found:
                return found

    # Import the whole family, so they show up as subclasses. Then return this
    # classes subclasses. This obviates the need to import everything at
    # initialization. It happens when needed, and only once.  Family members
    # must be in modules (files) in the same directory as the parent (me).
    # Furthermore, all the files in that directory will be imported. The only
    # exception is a file with the same name as myself, to avoid circular
    # imports. This is a private method, intended to be called when needed.

    @classmethod
    def family_children(self):

        # We only need to import the family once
        if not hasattr(self, '_family_imported'):

            # Find the location of the directory and the name of the module
            module = getmodule(self)
            directory = Path(module.__file__).parent
            module_name = module.__package__

            # Go through the directory and import everything into the module
            for import_file in directory.iterdir():
                if match(r'^[^_].*\.py$', import_file.name):
                    import_module(f'{module_name}.{import_file.stem}')

            # Prevent it from needing to run again
            self._family_imported = True

        # Return the subclasses (children)
        return self.__subclasses__()
