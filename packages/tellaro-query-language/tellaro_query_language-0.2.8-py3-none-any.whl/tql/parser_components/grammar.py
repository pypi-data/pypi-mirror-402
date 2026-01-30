"""TQL Grammar definitions using pyparsing."""

from pyparsing import (
    CaselessKeyword,
    Forward,
    Group,
    Literal,
)
from pyparsing import Optional as PyparsingOptional
from pyparsing import (
    QuotedString,
    Regex,
    Suppress,
    Word,
    ZeroOrMore,
    alphanums,
    alphas,
    delimitedList,
    infixNotation,
    nums,
    oneOf,
    opAssoc,
)


class TQLGrammar:
    """TQL grammar definitions.

    This class contains all the pyparsing grammar definitions for TQL,
    including tokens, operators, expressions, and special syntax.
    """

    def __init__(self):
        """Initialize all grammar elements."""
        self._setup_basic_tokens()
        self._setup_operators()
        self._setup_fields_and_values()
        self._setup_mutators()
        self._setup_comparisons()
        self._setup_special_expressions()
        self._setup_stats_expressions()
        self._setup_final_expressions()

    def _setup_basic_tokens(self):
        """Set up basic tokens and literals."""
        # Basic tokens
        self.identifier = Word(alphas, alphanums + "_.-")
        self.number = Word(nums + ".-")
        self.string_literal = QuotedString('"') | QuotedString("'")
        # CIDR notation for IP addresses (e.g., 192.168.1.0/24)
        self.cidr_notation = Word(nums + "./")
        # Define list items as strings, numbers, or identifiers
        self.list_item = self.string_literal | self.number | self.identifier
        self.list_literal = Group(Suppress("[") + delimitedList(self.list_item) + Suppress("]"))

        # Define simple values – note order matters (try string literals first, then CIDR)
        self.simple_value = self.string_literal | self.cidr_notation | self.number | self.identifier

        # Define type hints
        self.type_hint = oneOf("number int float decimal date array bool boolean geo object string", caseless=True)

    def _setup_operators(self):
        """Set up operator definitions."""
        # Define binary operators (require a value) - != must come before ! operators
        self.binary_ops = oneOf(
            "!= "  # != must be before ! operators
            + "!contains !in !startswith !endswith !regexp !cidr !is !between "
            + "regexp in contains = eq ne > gt >= gte < lt <= lte cidr is startswith endswith any all none",
            caseless=True,
        )

        # Define negated binary operators (using space-separated keywords or ! prefix)
        self.not_in_op = (CaselessKeyword("not") | "!") + CaselessKeyword("in")
        self.not_contains_op = (CaselessKeyword("not") | "!") + CaselessKeyword("contains")
        self.not_startswith_op = (CaselessKeyword("not") | "!") + CaselessKeyword("startswith")
        self.not_endswith_op = (CaselessKeyword("not") | "!") + CaselessKeyword("endswith")
        self.not_regexp_op = (CaselessKeyword("not") | "!") + CaselessKeyword("regexp")
        self.not_cidr_op = (CaselessKeyword("not") | "!") + CaselessKeyword("cidr")
        self.not_any_op = (CaselessKeyword("not") | "!") + CaselessKeyword("any")
        self.not_all_op = (CaselessKeyword("not") | "!") + CaselessKeyword("all")
        self.not_none_op = (CaselessKeyword("not") | "!") + CaselessKeyword("none")

        # Also support !contains, !startswith etc. as single tokens
        self.bang_in_op = Suppress("!") + CaselessKeyword("in")
        self.bang_contains_op = Suppress("!") + CaselessKeyword("contains")
        self.bang_startswith_op = Suppress("!") + CaselessKeyword("startswith")
        self.bang_endswith_op = Suppress("!") + CaselessKeyword("endswith")
        self.bang_regexp_op = Suppress("!") + CaselessKeyword("regexp")
        self.bang_cidr_op = Suppress("!") + CaselessKeyword("cidr")
        self.bang_any_op = Suppress("!") + CaselessKeyword("any")
        self.bang_all_op = Suppress("!") + CaselessKeyword("all")
        self.bang_none_op = Suppress("!") + CaselessKeyword("none")

        # Add between operator separately as it has special handling
        self.between_op = CaselessKeyword("between")
        self.not_between_op = (CaselessKeyword("not") | "!") + CaselessKeyword("between")
        self.bang_between_op = Suppress("!") + CaselessKeyword("between")

        # Define unary operators (no value required)
        self.unary_ops = oneOf("exists !exists", caseless=True)
        self.not_exists_op = (CaselessKeyword("not") | "!") + CaselessKeyword("exists")
        self.bang_exists_op = Suppress("!") + CaselessKeyword("exists")

        # Define is/is not operators
        self.is_op = CaselessKeyword("is")
        self.is_not_op = CaselessKeyword("is") + CaselessKeyword("not")
        self.bang_is_op = Suppress("!") + CaselessKeyword("is")

        # Define logical operators
        self.not_kw = CaselessKeyword("not") | "!"
        self.and_kw = CaselessKeyword("and")
        self.or_kw = CaselessKeyword("or")
        self.any_kw = CaselessKeyword("any")
        self.all_kw = CaselessKeyword("all")

    def _setup_fields_and_values(self):
        """Set up field and value definitions."""
        # Field names can contain single colons but we need to handle :: for type hints
        # We'll match the field name greedily but stop at ::
        self.field_name = Regex(r"[@a-zA-Z][@a-zA-Z0-9_.:-]*?(?=::|[^@a-zA-Z0-9_.:-]|$)")

    def _setup_mutators(self):
        """Set up mutator definitions."""
        # Define mutators
        self.mutator_name = oneOf(
            "lowercase uppercase trim split replace nslookup geoip_lookup geo "
            "length refang defang b64encode b64decode urldecode "
            "any all none avg average max min sum is_private is_global "
            "count unique first last",
            caseless=True,
        )
        # Mutator parameters can be either named (key=value) or positional (just value)
        # Named parameters: key=value where value can be string literal, list, identifier, or number
        self.mutator_named_param = Group(
            self.identifier + Suppress("=") + (self.string_literal | self.list_literal | self.identifier | self.number)
        )
        # Positional parameters can be strings (quoted or unquoted), numbers, or identifiers
        self.mutator_positional_param = self.string_literal | self.number | self.identifier
        self.mutator_param = self.mutator_named_param | self.mutator_positional_param
        self.mutator_params = Group(Suppress("(") + delimitedList(self.mutator_param) + Suppress(")"))
        self.mutator = Group(Suppress("|") + self.mutator_name + PyparsingOptional(self.mutator_params))
        self.mutator_chain = ZeroOrMore(self.mutator)

        # Field without mutators for geo expression
        self.typed_field_no_mutators = Group(self.field_name + PyparsingOptional(Suppress("::") + self.type_hint))

        # Field with optional type hint and mutators (field::type | mutator1 | mutator2)
        self.typed_field = Group(
            self.field_name + PyparsingOptional(Suppress("::") + self.type_hint) + self.mutator_chain
        )

        # Value with optional mutators (value | mutator1 | mutator2) or ('value' | mutator)
        self.simple_value_with_mutators = Group(self.simple_value + self.mutator_chain)
        self.parenthesized_value = Group(
            Suppress("(") + (self.string_literal | self.number | self.identifier) + self.mutator_chain + Suppress(")")
        )
        self.list_with_mutators = Group(self.list_literal + self.mutator_chain)
        self.value = (
            self.list_with_mutators
            | self.list_literal
            | self.parenthesized_value
            | self.simple_value_with_mutators
            | self.simple_value
        )

    def _setup_comparisons(self):
        """Set up comparison expressions."""
        # Standard comparison with field on left (field op value)
        self.std_comparison = Group(self.typed_field + self.binary_ops + self.value)

        # Between operator with field and list (field between [val1, val2])
        self.between_comparison_list = Group(self.typed_field + self.between_op + self.list_literal)

        # Between operator with natural syntax (field between val1 and val2)
        self.between_comparison_natural = Group(
            self.typed_field + self.between_op + self.simple_value + self.and_kw + self.simple_value
        )

        # Unary operations (field op)
        self.unary_comparison = Group(self.typed_field + self.unary_ops)

        # Negated operators
        self.negated_binary_comparison = Group(
            self.typed_field
            + (
                self.not_in_op
                | self.not_contains_op
                | self.not_startswith_op
                | self.not_endswith_op
                | self.not_regexp_op
                | self.not_cidr_op
                | self.not_any_op
                | self.not_all_op
                | self.not_none_op
                | self.bang_in_op
                | self.bang_contains_op
                | self.bang_startswith_op
                | self.bang_endswith_op
                | self.bang_regexp_op
                | self.bang_cidr_op
                | self.bang_any_op
                | self.bang_all_op
                | self.bang_none_op
            )
            + self.value
        )

        self.negated_unary_comparison = Group(self.typed_field + (self.not_exists_op | self.bang_exists_op))

        self.is_not_comparison = Group(self.typed_field + (self.is_not_op | self.bang_is_op) + self.simple_value)

        # Not between operators (both syntaxes)
        self.not_between_comparison_list = Group(
            self.typed_field + (self.not_between_op | self.bang_between_op) + self.list_literal
        )
        self.not_between_comparison_natural = Group(
            self.typed_field
            + (self.not_between_op | self.bang_between_op)
            + self.simple_value
            + self.and_kw
            + self.simple_value
        )

        # Define field list for reversed 'in' operator
        self.field_list_item = self.typed_field
        self.field_list = Group(Suppress("[") + delimitedList(self.field_list_item) + Suppress("]"))

        # Special case for 'in' operator - value in field(s)
        self.value_in_field = Group(self.value + CaselessKeyword("in") + self.typed_field)
        self.value_in_field_list = Group(self.value + CaselessKeyword("in") + self.field_list)

        # Field-first 'in' operator: field in [value1, value2, ...] (checks if field equals any value)
        # Add a marker "__field_in_values__" to distinguish from value_in_field
        self.field_in_values = Group(
            self.typed_field
            + CaselessKeyword("in")
            + self.list_literal
            + Literal("").setParseAction(lambda: "__field_in_values__")
        )
        self.field_not_in_values = Group(
            self.typed_field
            + (CaselessKeyword("not") | Literal("!"))
            + CaselessKeyword("in")
            + self.list_literal
            + Literal("").setParseAction(lambda: "__field_not_in_values__")
        )

    def _setup_special_expressions(self):
        """Set up special expressions like geo() and nslookup()."""
        # Forward declare for recursive use
        self.comparison_expr = Forward()

        # Define geo() parenthetical syntax
        self.geo_kw = CaselessKeyword("geo") | CaselessKeyword("geoip_lookup")
        self.geo_conditions = Forward()

        # Define geo parameters
        self.geo_param_name = Word(alphas, alphanums + "_")
        self.geo_param_value = (
            CaselessKeyword("true")
            | CaselessKeyword("false")
            | QuotedString('"', escChar="\\")
            | QuotedString("'", escChar="\\")
            | Regex(r"\d+")
        )
        self.geo_param = Group(self.geo_param_name + Suppress("=") + self.geo_param_value)
        self.geo_params = PyparsingOptional(Suppress(",") + delimitedList(self.geo_param))

        # Support multiple geo syntax patterns
        self.geo_empty = Group(
            self.typed_field_no_mutators + Suppress("|") + self.geo_kw + Suppress("(") + Suppress(")")
        )

        self.geo_params_only = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.geo_kw
            + Suppress("(")
            + delimitedList(self.geo_param)
            + Suppress(")")
        )

        self.geo_conditions_only = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.geo_kw
            + Suppress("(")
            + self.geo_conditions
            + Suppress(")")
        )

        self.geo_conditions_and_params = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.geo_kw
            + Suppress("(")
            + self.geo_conditions
            + Suppress(",")
            + delimitedList(self.geo_param)
            + Suppress(")")
        )

        self.geo_params_and_conditions = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.geo_kw
            + Suppress("(")
            + delimitedList(self.geo_param)
            + Suppress(",")
            + self.geo_conditions
            + Suppress(")")
        )

        # Combine all geo expression patterns
        self.geo_mutator_expr = (
            self.geo_params_and_conditions
            | self.geo_conditions_and_params
            | self.geo_conditions_only
            | self.geo_params_only
            | self.geo_empty
        )

        # Define nslookup() parenthetical syntax
        self.nslookup_kw = CaselessKeyword("nslookup")
        self.nslookup_conditions = Forward()

        # Define nslookup parameters
        self.nslookup_param_name = Word(alphas, alphanums + "_")
        self.nslookup_param_value = (
            CaselessKeyword("true")
            | CaselessKeyword("false")
            | QuotedString('"', escChar="\\")
            | QuotedString("'", escChar="\\")
            | self.list_literal
            | Regex(r"\d+")
        )
        self.nslookup_param = Group(self.nslookup_param_name + Suppress("=") + self.nslookup_param_value)
        self.nslookup_params = PyparsingOptional(Suppress(",") + delimitedList(self.nslookup_param))

        # Support multiple nslookup syntax patterns
        self.nslookup_empty = Group(
            self.typed_field_no_mutators + Suppress("|") + self.nslookup_kw + Suppress("(") + Suppress(")")
        )

        self.nslookup_params_only = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.nslookup_kw
            + Suppress("(")
            + delimitedList(self.nslookup_param)
            + Suppress(")")
        )

        self.nslookup_conditions_only = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.nslookup_kw
            + Suppress("(")
            + self.nslookup_conditions
            + Suppress(")")
        )

        self.nslookup_conditions_and_params = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.nslookup_kw
            + Suppress("(")
            + self.nslookup_conditions
            + Suppress(",")
            + delimitedList(self.nslookup_param)
            + Suppress(")")
        )

        self.nslookup_params_and_conditions = Group(
            self.typed_field_no_mutators
            + Suppress("|")
            + self.nslookup_kw
            + Suppress("(")
            + delimitedList(self.nslookup_param)
            + Suppress(",")
            + self.nslookup_conditions
            + Suppress(")")
        )

        # Combine all nslookup expression patterns
        self.nslookup_mutator_expr = (
            self.nslookup_params_and_conditions
            | self.nslookup_conditions_and_params
            | self.nslookup_conditions_only
            | self.nslookup_params_only
            | self.nslookup_empty
        )

    def _setup_stats_expressions(self):
        """Set up statistics expressions."""
        # Define stats expressions
        self.stats_kw = CaselessKeyword("stats")
        self.by_kw = CaselessKeyword("by")

        # Aggregation function names - including aliases
        self.agg_function_name = oneOf(
            "count unique_count sum min max average avg median med std standard_deviation "
            "percentile percentiles p pct percentile_rank percentile_ranks pct_rank pct_ranks "
            "values unique cardinality",
            caseless=True,
        )

        # Special case for count(*) and count()
        self.count_all = CaselessKeyword("count") + Suppress("(") + Suppress("*") + Suppress(")")
        self.count_empty = CaselessKeyword("count") + Suppress("(") + Suppress(")")

        # Aggregation function with field
        self.agg_function = (
            Group(
                self.agg_function_name
                + Suppress("(")
                + self.field_name
                + PyparsingOptional(
                    Suppress(",") + (oneOf("top bottom", caseless=True) + self.number | delimitedList(self.number))
                )
                + Suppress(")")
            )
            | self.count_all
            | self.count_empty
        )

        # Support for aliasing: sum(revenue) as total_revenue
        self.as_kw = CaselessKeyword("as")
        self.agg_with_alias = Group(self.agg_function + PyparsingOptional(self.as_kw + self.identifier))

        # Multiple aggregations separated by commas
        self.agg_list = delimitedList(self.agg_with_alias)

        # Group by fields with optional "top N" for each field
        self.top_kw = CaselessKeyword("top")
        self.group_by_field_with_bucket = Group(self.field_name + PyparsingOptional(self.top_kw + self.number))
        self.group_by_fields = delimitedList(self.group_by_field_with_bucket)

        # Visualization hint: => chart_type
        self.viz_arrow = Literal("=>")
        self.viz_types = oneOf(
            "bar barchart line area pie donut scatter heatmap treemap sunburst "
            "table number gauge map grouped_bar stacked_bar nested_pie nested_donut chord",
            caseless=True,
        )
        self.viz_hint = PyparsingOptional(self.viz_arrow + self.viz_types)

        # Complete stats expression: | stats agg_functions [by group_fields] [=> viz_type]
        self.stats_expr_with_pipe = Group(
            Suppress("|")
            + self.stats_kw
            + self.agg_list
            + PyparsingOptional(self.by_kw + self.group_by_fields)
            + self.viz_hint
        )

        # Stats expression without pipe (for standalone use)
        self.stats_expr_no_pipe = Group(
            self.stats_kw + self.agg_list + PyparsingOptional(self.by_kw + self.group_by_fields) + self.viz_hint
        )

        # Combined stats expression (with or without pipe)
        self.stats_expr = self.stats_expr_with_pipe | self.stats_expr_no_pipe

    def _setup_final_expressions(self):
        """Set up final expression definitions."""
        # Define all forms of comparison
        self.comparison_expr << (
            self.negated_binary_comparison
            | self.negated_unary_comparison
            | self.is_not_comparison
            | self.not_between_comparison_natural
            | self.not_between_comparison_list
            | self.field_not_in_values  # field not in [values] - must come before std_comparison
            | self.field_in_values  # field in [values] - must come before std_comparison
            | self.std_comparison
            | self.between_comparison_natural
            | self.between_comparison_list
            | self.unary_comparison
            | self.value_in_field_list
            | self.value_in_field
            | self.typed_field
        )

        # Create a combined expression that includes regular comparisons, geo, and nslookup expressions
        self.base_expr = self.geo_mutator_expr | self.nslookup_mutator_expr | self.comparison_expr

        # Define filter expression with operator precedence
        self.filter_expr = infixNotation(
            self.base_expr,
            [
                (self.not_kw, 1, opAssoc.RIGHT),
                (self.and_kw, 2, opAssoc.LEFT),
                (self.or_kw, 2, opAssoc.LEFT),
            ],
        )

        # Define the complete TQL expression
        self.tql_expr = Forward()
        self.tql_expr << (
            # filter | stats
            (
                self.stats_expr_no_pipe  # just stats without pipe (applies to all records)
                | Group(self.filter_expr + self.stats_expr_with_pipe)  # filter | stats
                | self.stats_expr  # just stats with pipe (applies to all records)
                | self.filter_expr
            )  # just filter (no stats)
        )

        # Define geo_conditions and nslookup_conditions
        self.geo_conditions << infixNotation(
            self.comparison_expr,
            [
                (self.not_kw, 1, opAssoc.RIGHT),
                (self.and_kw, 2, opAssoc.LEFT),
                (self.or_kw, 2, opAssoc.LEFT),
            ],
        )

        self.nslookup_conditions << infixNotation(
            self.comparison_expr,
            [
                (self.not_kw, 1, opAssoc.RIGHT),
                (self.and_kw, 2, opAssoc.LEFT),
                (self.or_kw, 2, opAssoc.LEFT),
            ],
        )
