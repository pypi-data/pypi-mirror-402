from pathlib import Path
from typing import Optional,Literal

def check_bom(data: bytes) -> Optional[str]:
    """Check for Byte Order Mark in binary data."""
    if data.startswith(b'\xEF\xBB\xBF'):  # UTF-8 BOM
        return 'utf-8-sig'
    if data.startswith(b'\xFF\xFE'):      # UTF-16 LE
        return 'utf-16'
    if data.startswith(b'\xFE\xFF'):      # UTF-16 BE
        return 'utf-16'
    return None

def detect_encoding(
    path: Path | str, 
    sample_size: int = 65536, 
    ignore_errors: bool = False
) -> Optional[str]:
    """Detect file encoding using BOM and chardet."""
    path = Path(path)
    
    try:
        import chardet
        
        with path.open('rb') as f:
            raw_data = f.read(sample_size)
        
        if bom_encoding := check_bom(raw_data):
            return bom_encoding
        
        result = chardet.detect(raw_data)
        
        if result['confidence'] < 0.7:
            return 'utf-8'
            
        return result['encoding'] or 'utf-8'
    
    except ImportError:
        raise ImportError("Install chardet for automatic encoding detection")
    except Exception:
        if ignore_errors:
            return None
        raise

def determine_minimal_encoding(content: str) -> Literal["ascii","cp1251","utf-8"]:
    """Determine the minimal encoding that supports the content."""
    try:
        content.encode('ascii')
        return 'ascii'
    except UnicodeEncodeError:
        pass
    
    try:
        content.encode('cp1251')
        return 'cp1251'
    except UnicodeEncodeError:
        pass

    return 'utf-8'