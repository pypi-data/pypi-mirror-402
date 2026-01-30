class FakeObj:
    """A stub class that absorbs any calls. Return when the functionality is not available on this OS."""
    
    def __getattr__(self, name):
        return self
    
    def __call__(self, *args, **kwargs):
        return self
    
    def __getitem__(self, key):
        return self
    
    def __setattr__(self, name, value):
        pass
    
    def __iter__(self):
        return iter([])
    
    def __next__(self):
        raise StopIteration
    
    def __len__(self):
        return 0
    
    def __str__(self):
        return "<Fake>"
    
    def __repr__(self):
        return "<Fake>"
    
    def __bool__(self):
        return False