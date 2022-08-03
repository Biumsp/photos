#%% 
import functools

from sqlalchemy import func

def can_fail_silently(funk=None, default=False, callback=None):
    '''
    Adds the option "fail_silently" to the function:
        if fail_silently=True, any exception in the function
        will be catched and a 'failed' will be returned
    '''

    # This way you can apply it with the @ notation
    if funk is None:
        return functools.partial(can_fail_silently, default=default, callback=callback)

    @functools.wraps(funk)
    def wrapper_can_fail_silently(*args, fail_silently=default, **kwargs):

        try: return funk(*args, **kwargs)
        except Exception as e:
            try: 
                return callback(*args, **kwargs)
            except: 
                if fail_silently: return 'failed'
                else: raise e

    return wrapper_can_fail_silently


@can_fail_silently
def failfunk():
    int('a')

#%%


print(failfunk(fail_silently=True), 1)
print(failfunk(), 2)

# %%
