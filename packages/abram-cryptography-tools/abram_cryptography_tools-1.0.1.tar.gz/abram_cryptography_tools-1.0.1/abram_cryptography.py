import itertools

def shift(text, mode, *keys, ):
    
    result=""
    
    keys=list(keys)
    
    key_stream=itertools.cycle(keys)
    
    
    for char in text:
        
        char_level = ord(char)
        
        char_level -= 32
        
        if mode=="encode":
            char_level += next(key_stream)
        elif mode=="decode":
            char_level -= next(key_stream)
        else:
            print("not a choice")
            return
        
        new_char_level=char_level%95
        
        final_char_level=new_char_level+32
        
        final_char=chr(final_char_level)
        
        result+=final_char
    
    return result
    