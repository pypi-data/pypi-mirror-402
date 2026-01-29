
class HybridMethod:
    """
    A descriptor that invokes different methods when called on the class
    versus when called on an instance.
    """
    def __init__(self, fclass, finstance=None):
        self.fclass = fclass
        self.finstance = finstance

    def __get__(self, instance, owner):
        if instance is None:
            return self.fclass.__get__(owner, owner)
        return self.finstance.__get__(instance, owner)

    def instance_method(self, finstance):
        """
        Decorator to register the instance method.
        """
        self.finstance = finstance
        return self
