package jobs

import "context"

type JobState string

const (
	StateActive   JobState = "active"
	StateTerminal JobState = "terminal"
)

type CancelJobRequest struct {
	JobID string
}

type Event struct {
	JobID string
	Name  string
}

type Service struct {
	states map[string]JobState
	events []Event
}

func NewService(states map[string]JobState) *Service {
	ownedStates := make(map[string]JobState, len(states))
	for id, state := range states {
		ownedStates[id] = state
	}
	return &Service{states: ownedStates}
}

func (s *Service) CancelJob(_ context.Context, req CancelJobRequest) error {
	if req.JobID == "" {
		return ErrMissingJobID
	}
	if s.states[req.JobID] == StateTerminal {
		return nil
	}
	s.states[req.JobID] = StateTerminal
	s.events = append(s.events, Event{JobID: req.JobID, Name: "JobCancelled"})
	return nil
}

func (s *Service) PublishedEvents() []Event {
	return append([]Event(nil), s.events...)
}
