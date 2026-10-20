# GitLab Duo activation and demo

## Integration status
The flow YAML is source configuration, not proof of activation. No successful
Duo session is claimed by this document. Update this section only with an actual
catalog item URL, session URL, and MR note after running it.

## Configure
1. In this project's AI > Flows (or Explore > AI Catalog > Flows), create a flow
   managed by this project. Use a descriptive human-selected display name.
2. Paste `.gitlab/duo/flows/migration-review.yaml` as its configuration.
3. Enable the flow for this project and add the mention trigger. The service
   account handle is assigned by GitLab; do not invent it.
4. On an MR with completed CI, mention that actual handle and request migration
   acceptance review. The trigger passes project and MR context.
5. Verify AI > Sessions and the posted MR evidence note. Capture the URLs here.

The flow only reads evidence and posts a bounded explanation. It cannot execute
shell commands, edit repository files, merge, or deploy through its toolset.
The publisher independently rereads the job evidence and current MR head SHA.
Review API tool permissions when enabling the flow; prompts alone are not a
security boundary. The configuration is scoped to showcase project 87486337.

## Demonstrate the difference
1. Run a pipeline with input `migration_scenario=breaking`. The release job fails even
   though the migration and v2 probes pass. Show old/mixed/app-rollback failures.
2. Request Duo's evidence explanation on the MR using current job evidence.
3. Use the expand fixture and rerun. All declared checks must pass.
4. Show the JSON/HTML artifacts and Duo's scoped explanation.

For the mention-based flow, a pipeline must be associated with the MR head SHA.
The agent must report INCONCLUSIVE if only an unrelated or stale pipeline exists.

## Submission evidence to collect
- Actual CI URLs for both selected-scenario outcomes.
- Actual Duo catalog/session and MR note URLs.
- Under-three-minute English demo explaining audience, failure, fix, and limits.
- MIT license and publicly visible pipeline history.

## Official references
- https://docs.gitlab.com/user/duo_agent_platform/flows/custom/
- https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/
- https://docs.gitlab.com/user/duo_agent_platform/flows/execution/
- https://gitlab-transcend.devpost.com/rules

Registry/tool names were checked against GitLab's public AI Gateway repository.
Runtime schema/tool availability still needs verification on the hackathon group.
