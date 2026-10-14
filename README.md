# Cartograph

An offline prototype that turns a small behavior contract into a generated Go integration test through a provider interface.

**Status:** prototype · **Runtime:** Python 3.11+ and Go 1.22+ · **Network/API key:** not required for the demo

## What it does

Cartograph reads a JSON contract containing one service behavior, plans that scenario, and asks a provider implementation for a Go test. The included deterministic fixture provider emits a transparent example test for a demo Go service. It is a reproducible contract-to-test slice, not an LLM agent or a production test-generation platform.

## Demo

From this directory, run:

```powershell
python -m cartograph plan samples/contracts/cancel_job.json
python -m cartograph generate samples/contracts/cancel_job.json --scenario terminal-no-event --provider fixture --output demo/cartograph_generated_test.go
Push-Location demo
go test ./...
Pop-Location
```

The generated test checks that cancelling a terminal job does not publish another event. The test is included as an inspectable example file; the generation command deterministically recreates it.

## Architecture

`cartograph.contracts` validates and loads the JSON input. `cartograph.planner` turns declared behavior cases into named scenarios. `cartograph.providers.TestProvider` is the generation boundary. `FixtureProvider` is a local deterministic implementation that renders one explicitly supported demo case. The generated test runs against a small Go service in `demo/`.

## Design decisions and trade-offs

- Use the Python standard library so the demo is offline and setup stays small.
- Keep the provider interface separate from the fixture. A future model-backed provider can be added without claiming that this prototype already calls a model.
- Use one declared behavior and one fixture to make the contract, generated assertion, and failure mode easy to inspect. This sacrifices breadth and retrieval quality for a verifiable first slice.
- The Go test is the verifier. This prototype does not yet sandbox arbitrary generated code.

## Authorship and contributions

Created with AI coding assistance under Kausthubh’s direction and published as a portfolio prototype on 14 October 2026. Review the source, tests and current limitations; this prototype has no production use or performance claim. The broader Cartograph architecture in the design specification is not implemented here. No employer source, private service code, or production data is included.

## Upstream credits

The prototype uses only the Python standard library and Go standard library. No external code, templates, or datasets are bundled. The behavior contract and demo service are original examples written for this prototype.

## Requirements and reproducible commands

- Python 3.11 or later
- Go 1.22 or later

Run the Python unit suite:

```powershell
python -m unittest discover -s tests -v
```

Regenerate and verify the offline demo:

```powershell
python -m cartograph generate samples/contracts/cancel_job.json --scenario terminal-no-event --provider fixture --output demo/cartograph_generated_test.go
Push-Location demo
go test ./...
Pop-Location
```

All commands run locally without credentials or external services.

## Verification and results

Verified locally on 14 October 2026 with Python 3.14.2 and Go 1.25.12 on Windows/amd64: `python -m unittest discover -s tests -v` passed all 5 tests, including a Go integration check that passes for the expected behavior and fails after an event-publication regression is injected. `go test ./...` passed in the demo module. These results cover the deterministic fixture only; they do not establish model accuracy, generation quality, latency, cost, or production adoption.

## Limitations and failure cases

- Only one declared scenario and one fixture output are supported.
- The provider does not use an LLM; it is a deterministic renderer used to exercise the interface and offline workflow.
- No source indexing, semantic retrieval, PR diff analysis, compile-and-repair loop, mutation testing, calibrated judge, CI release gate, MCP server, tracing, or cost ledger exists in this prototype.
- The verifier runs the demo's Go tests directly and is not safe for untrusted repositories or generated code.

## Roadmap

Potential next steps include multiple contract scenarios, a safe verifier boundary, human-labeled evaluation examples, and an optional real model provider. These are plans, not current features.

## License

No license has been selected yet. Until a license file is added, reuse and redistribution permissions are not granted by this repository.
