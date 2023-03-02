#!/usr/bin/python3

class Error(Exception):
    """Base class for errors in this module"""
    pass
    
class TransformError(Error):
    """Errors raised by transformers."""
    pass

class Transformer():
    """
    Base class used to transform a basetree into a different format.
    
    Attributes:
    -----------
    
    script (fnc):
        The function used to transform each tree. Returns tree.s
    
    Methods:
    --------
    
    script_error(self, msg):
        Called by script function in case of error.
    
    transform(self, forest):
        Applies the transformations given in self.script to each tree in
        a BaseForest.
        
    """
    
    def __init__(self):
        self.script = script
        
    def script_error(self, msg, e = None):
        """Called by script in case of error."""
        if e:
            print(msg)
            raise e
        else:
            raise TransformError(msg)
    
    def transform(self, forest, **kwargs):
        """
        transform(self, forest):
            Applies the transformations given in self.script to each tree in
            a BaseForest. Returns forest.
            
        Parameters:
            forest (treetools.basetree.BaseForest):
                The forest to be transformed.
            **kwargs:
                **kwargs to be passed to self.script.
                
        Returns:
            transform(self, forest, **kwargs) :
                A treetools.basetree.BaseForest instance.
        """
        for i, stree in enumerate(forest):
            if len(forest) > 1000 and float(i/1000) == int(i/1000):
                print('Transforming tree {} of {}'.format(str(i), len(forest)))
            old_id = stree.get_id()
            tree = stree.to_base_tree()
            # Self passed explicitly because it's a FUNCTION not a METHOD.
            try:
                tree = self.script(self, tree, **kwargs)
            except Exception as e:
                self.script_error('Error transforming tree:\n' + stree, e)
            try:
                forest[i] = tree.to_string_tree()
            except:
                # Revert to the old_id
                stree.update_id(old_id)
                forest[i] = tree.to_string_tree()
        return forest
        
            
def script(transformer, tree, **kwargs):
    """
    Applies the transformations given in script to each tree in
    a BaseForest. This function should be updated for each instance
    depending on the transformation required.
    
    Parameters:
        transformer (treetools.transformer.Transformer):
            An instance of the transformer object.
        tree (treetools.basetree.BaseTree):
            The tree to be transformed.
        **kwargs:
            All further arguments must be keyword arguments.
    """
    # The default method does nothing expect return the tree
    return tree
        
    
