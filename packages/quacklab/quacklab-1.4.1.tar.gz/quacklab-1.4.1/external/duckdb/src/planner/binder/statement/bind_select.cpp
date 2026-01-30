#include "duckdb/parser/statement/select_statement.hpp"
#include "duckdb/planner/binder.hpp"
#include "duckdb/planner/bound_query_node.hpp"

#include "duckdb/hinting/planner_hints.hpp"  // !!! quacklab addition

namespace duckdb {

BoundStatement Binder::Bind(SelectStatement &stmt) {
	auto &properties = GetStatementProperties();
	properties.allow_stream_result = true;
	properties.return_type = StatementReturnType::QUERY_RESULT;

	// !!! quacklab addition

	// We have to first bind the select statement before we can parse our hints.
	// This is because the binder will recurse to the base tables and determine their relation IDs
	// We need this information as part of the hint parsing process.
	auto bound = Bind(*stmt.node);
	auto planner_hints = tud::HintingContext::CurrentPlannerHints();
	planner_hints->ParseHints();

	// !!! end quacklab addition

	return bound; // !!! quacklab modification: Bind(*stmt.node);
}

} // namespace duckdb
