
# Tree-sitter queries for TLDR analysis

QUERIES = {
    "symbols": {
        "python": """
            (function_definition
              name: (identifier) @function.name) @function.def
            (class_definition
              name: (identifier) @class.name) @class.def
        """,
        "javascript": """
            (function_declaration
              name: (identifier) @function.name) @function.def
            (function) @function.def
            (class_declaration
              name: (type_identifier) @class.name) @class.def
            (method_definition
              name: (property_identifier) @method.name) @method.def
            
            (variable_declarator
              name: (identifier) @var.name
              value: (arrow_function)) @function.def

            (arrow_function) @function.def
            
            (interface_declaration
              name: (type_identifier) @interface.name) @interface.def
            (type_alias_declaration
              name: (type_identifier) @type.name) @type.def
            (enum_declaration
              name: (identifier) @enum.name) @enum.def
        """,
        "typescript": """
            (function_declaration
              name: (identifier) @function.name) @function.def
            (function) @function.def
            (class_declaration
              name: (type_identifier) @class.name) @class.def
            (method_definition
              name: (property_identifier) @method.name) @method.def
            
            (variable_declarator
              name: (identifier) @var.name
              value: (arrow_function)) @function.def

            (arrow_function) @function.def
            
            (interface_declaration
              name: (type_identifier) @interface.name) @interface.def
            (type_alias_declaration
              name: (type_identifier) @type.name) @type.def
            (enum_declaration
              name: (identifier) @enum.name) @enum.def
        """,
        "go": """
            (function_declaration
              name: (identifier) @function.name) @function.def
            (method_declaration
              name: (field_identifier) @method.name) @method.def
            (type_declaration
              (type_spec
                name: (type_identifier) @type.name)) @type.def
        """,
        "rust": """
            (function_item
              name: (identifier) @function.name) @function.def
            (struct_item
              name: (type_identifier) @struct.name) @struct.def
            (enum_item
              name: (type_identifier) @enum.name) @enum.def
            (impl_item
              type: (type_identifier) @impl.type) @impl.def
        """
    },
    "calls": {
        "python": """
            (call
              function: (identifier) @call.name)
            (call
              function: (attribute
                attribute: (identifier) @call.name))
        """,
        "javascript": """
            (call_expression
              function: (identifier) @call.name)
            (call_expression
              function: (member_expression
                property: (property_identifier) @call.name))
        """,
        "typescript": """
            (call_expression
              function: (identifier) @call.name)
            (call_expression
              function: (member_expression
                property: (property_identifier) @call.name))
        """,
        "go": """
            (call_expression
              function: (identifier) @call.name)
            (call_expression
              function: (selector_expression
                field: (field_identifier) @call.name))
        """,
        "rust": """
            (call_expression
              function: (identifier) @call.name)
            (call_expression
              function: (field_expression
                field: (field_identifier) @call.name))
        """
    },
    "complexity": {
        "python": """
             (if_statement) @branch
             (for_statement) @branch
             (while_statement) @branch
             (except_clause) @branch
             (with_statement) @branch
             (boolean_operator) @branch
        """,
        "javascript": """
             (if_statement) @branch
             (for_statement) @branch
             (for_in_statement) @branch
             (for_of_statement) @branch
             (while_statement) @branch
             (do_statement) @branch
             (case_clause) @branch
             (catch_clause) @branch
             (ternary_expression) @branch
             (binary_expression operator: ["&&", "||"]) @branch
        """,
        "typescript": """
             (if_statement) @branch
             (for_statement) @branch
             (for_in_statement) @branch
             (for_of_statement) @branch
             (while_statement) @branch
             (do_statement) @branch
             (case_clause) @branch
             (catch_clause) @branch
             (ternary_expression) @branch
             (binary_expression operator: ["&&", "||"]) @branch
        """,
        "go": """
             (if_statement) @branch
             (for_statement) @branch
             (expression_switch_statement) @branch
             (type_switch_statement) @branch
             (select_statement) @branch
        """,
        "rust": """
             (if_expression) @branch
             (for_expression) @branch
             (while_expression) @branch
             (match_arm) @branch
             (loop_expression) @branch
        """
    }
}
