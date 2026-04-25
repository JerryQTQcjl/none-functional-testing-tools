## ADDED Requirements

### Requirement: Dependency graph construction
The system SHALL construct a dependency graph from code analysis, representing relationships between modules, classes, and methods.

#### Scenario: Static dependency analysis
- **WHEN** a code repository is scanned for the first time
- **THEN** the system SHALL parse import/module statements to build a dependency graph
- **AND** identify direct dependencies between code components
- **AND** store the graph in Neo4j for efficient traversal

#### Scenario: Incremental graph updates
- **WHEN** code changes are merged to the main branch
- **THEN** the system SHALL update only the affected portions of the dependency graph
- **AND** maintain graph consistency with the updated codebase

### Requirement: Change impact calculation
The system SHALL calculate the impact scope of code changes by traversing the dependency graph.

#### Scenario: Direct impact identification
- **WHEN** a file, class, or method is modified
- **THEN** the system SHALL identify all components that directly depend on the changed element
- **AND** include these in the direct impact set

#### Scenario: Transitive impact identification
- **WHEN** calculating impact scope
- **THEN** the system SHALL traverse the dependency graph to find transitive dependencies
- **AND** include indirectly affected components up to a configurable depth (default: 3 levels)

#### Scenario: Change scope from diff
- **WHEN** a pull request or commit is analyzed
- **THEN** the system SHALL parse the git diff to identify changed files and methods
- **AND** calculate impact scope based on the dependency graph

### Requirement: Risk assessment for changes
The system SHALL assign a risk score to code changes based on multiple factors.

#### Scenario: Risk score calculation
- **WHEN** a change's impact scope is calculated
- **THEN** the system SHALL compute a risk score considering:
  - Size of the impact scope (number of affected components)
  - Code complexity metrics (cyclomatic complexity, nesting depth)
  - Historical defect density of affected modules
  - Test coverage level of changed code
- **AND** return a risk score from 0-100

#### Scenario: Risk categorization
- **WHEN** a risk score is calculated
- **THEN** the system SHALL categorize the risk as Low (0-30), Medium (31-60), High (61-80), or Critical (81-100)
- **AND** display the category with visual indicators in the UI

### Requirement: Impact analysis visualization
The system SHALL provide visual representations of impact analysis results.

#### Scenario: Dependency graph visualization
- **WHEN** a user views impact analysis results
- **THEN** the system SHALL display an interactive graph showing:
  - Changed nodes highlighted in red
  - Directly impacted nodes in orange
  - Transitively impacted nodes in yellow
- **AND** allow drill-down to view dependency details

#### Scenario: Impact tree view
- **WHEN** a user views impact analysis in tree format
- **THEN** the system SHALL display a hierarchical tree of affected components
- **AND** group by module, package, and class levels
- **AND** show the dependency distance from the changed code

### Requirement: Dynamic call chain analysis
The system SHALL enhance dependency graphs with runtime call chain data.

#### Scenario: Call chain collection
- **WHEN** tests are executed with instrumentation enabled
- **THEN** the system SHALL collect actual method call chains during execution
- **AND** merge this data with the static dependency graph

#### Scenario: Dynamic dependency discovery
- **WHEN** runtime calls are discovered that don't exist in static analysis
- **THEN** the system SHALL add these as dynamic dependencies to the graph
- **AND** mark them separately from static dependencies for analysis accuracy

### Requirement: Impact analysis API
The system SHALL provide REST APIs for impact analysis queries.

#### Scenario: On-demand impact analysis
- **WHEN** a client requests impact analysis for a commit SHA
- **THEN** the system SHALL return the impact scope and risk score within 10 seconds for typical repositories
- **AND** include lists of affected components by level

#### Scenario: Batch analysis
- **WHEN** a client requests impact analysis for multiple commits
- **THEN** the system SHALL process requests in parallel
- **AND** return results for all commits within 30 seconds
