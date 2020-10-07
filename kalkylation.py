from decimal import Decimal, ROUND_HALF_EVEN
from functools import partial

from sympy import solve, Eq
from sympy.core import N
from sympy.core.numbers import Number
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import parse_expr
from sympy.parsing.sympy_tokenize import generate_tokens


class Kalkylation:
    """
        >>> Kalkylation("1 2\\n3")
        Input: 1 + 2 + 3
        Symbolic result: 6
        Numeric result: 6.00
        
        >>> k = Kalkylation("1 = 2+x")
        >>> k
        Input: 1 = 2 + x
        Symbolic result: -1
        Numeric result: -1.00
        
        >>> k.tokens
        ['1', '=', '2', '+', 'x']
        
        >>> Kalkylation.result_decimals = '.000001'
        
        >>> Kalkylation("1+23 =3+x**2")
        Input: 1 + 23 = 3 + x ** 2
        Symbolic result: -sqrt(21), sqrt(21)
        Numeric result: -4.582576, 4.582576
        
    """
    
    result_decimals = '.01'
    
    def __init__(self, input_text):
        input_text = self._maybe_add_plusses(input_text)
        
        if '=' in input_text:
            left, right = input_text.split('=', 1)
            results = solve(Eq(parse_expr(left), parse_expr(right)))
        else:
            left = input_text
            right = []
            results = parse_expr(left)
        
        self.tokens = self._tokenize(left)
        if left and right:
            self.tokens.append('=')
        self.tokens.extend(self._tokenize(right))
        self.as_text = ' '.join(self.tokens)
        
        if not isinstance(results, list):
            results = [results]
        self.symbolic = results
        self.numeric = [
            Decimal(str(N(result))).quantize(
                Decimal(self.result_decimals),
                rounding=ROUND_HALF_EVEN
            ) for result in results]
    
    def __repr__(self):
        return (
            f"Input: {self.as_text}\n"
            f"Symbolic result: {', '.join(list(map(str, self.symbolic)))}\n"
            f"Numeric result: {', '.join(list(map(str, self.numeric)))}"
        )
    
    @staticmethod    
    def _maybe_add_plusses(as_text):
        """
            >>> Kalkylation._maybe_add_plusses("1 2.0\\n3")
            '1+2.0+3'
            >>> Kalkylation._maybe_add_plusses("1 + 2\\n3")
            '1 + 2 3'
        """
        parts = as_text.split()
        try:
            [Number(part) for part in parts]
            as_text = "+".join(parts)
        except SympifyError:
            as_text = ' '.join(parts)
        return as_text
 
    @staticmethod
    def _tokenize(as_text):
        """
            >>> Kalkylation._tokenize("1+ 23 ")
            ['1', '+', '23']
        """
        tokens = [
            token[1] for token
            in generate_tokens(
                partial(next, iter([as_text]))
            )
            if token[1].strip()
        ]
        return tokens

