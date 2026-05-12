from core.analysis.complexity import analyze_complexity
from core.analysis.printer import print_expr_tree
from core.compiler.optimizer.canonicalize import canonicalize
from core.compiler.optimizer.passes import optimize
from core.compiler.pass_manager import PassManager
from core.compiler.type_checker import infer_type
from core.compiler.wgsl.backend import WGSLBackend
from core.ir.graph import Universe
from core.ir.math_expr import Constant
from core.ir.scene_nodes import MaterialNode, SphereNode, Transform, UnionNode
from core.parser.lower_to_ir import parse_string_to_ir
from core.runtime.validation import validate_expr
from core.serialization.json_export import export_universe


def run_pipeline_demo():
    print("--- SYSTEM: Pipeline Initialization ---")
    pm = PassManager()

    # Type Inference
    pm.add_pass("Type Inference", infer_type)

    # Semantic Validation
    def _validation_pass(expr):
        validate_expr(expr)
        return expr

    pm.add_pass("Semantic Validation", _validation_pass)

    #  Canonicalization
    pm.add_pass("Canonicalization", canonicalize)

    #  Optimization
    pm.add_pass("Optimization", optimize)

    #  Complexity Analysis
    def _complexity_pass(expr):
        analyze_complexity(expr)
        return expr

    pm.add_pass("Complexity Analysis", _complexity_pass)

    input_str = "sqrt(x*x + y*y + z*z) - 10 + (2 * 0)"
    print(f"Input string: {input_str}\n")

    # Lowering (Parsing)
    ir_expr = parse_string_to_ir(input_str)

    # Run the pipeline
    final_ir = pm.run(ir_expr)

    print("--- Analysis: Expression Tree ---")
    print(print_expr_tree(final_ir))

    pm.print_diagnostics()

    print("\n--- SYSTEM: WGSL Backend (Expression) ---")
    backend = WGSLBackend()
    wgsl_expr_ast = backend.compile_expr(final_ir)
    print(f"WGSL AST Emission: {wgsl_expr_ast.emit()}")

    print("\n--- SYSTEM: Scene Graph Compilation ---")
    sphere1 = SphereNode(
        radius=Constant(value=10.0),
        transform=Transform(position=(0.0, 0.0, 0.0)),
        material=MaterialNode(id=1, color=(1.0, 0.0, 0.0)),
    )
    sphere2 = SphereNode(
        radius=Constant(value=5.0),
        transform=Transform(position=(20.0, 0.0, 0.0)),
        material=MaterialNode(id=2, color=(0.0, 1.0, 0.0)),
    )
    union_node = UnionNode(left=sphere1, right=sphere2)

    scene_ast = backend.compile_scene(union_node)
    scene_source = backend.emit_source(scene_ast)
    print(f"Scene WGSL:\n{scene_source}")

    print("\n--- SYSTEM: JSON Serialization ---")
    universe = Universe(nodes=[union_node])
    json_data = export_universe(universe)
    print(f"Serialized Universe:\n{json_data[:400]}...")


if __name__ == "__main__":
    run_pipeline_demo()
