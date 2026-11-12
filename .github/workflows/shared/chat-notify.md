---
safe-outputs:
  jobs:
    slack-notify:
      description: "Post a short security summary to Slack (mrkdwn: *bold*, <url|text>, no tables)."
      runs-on: ubuntu-26.04
      output: "Slack notification sent"
      inputs:
        message:
          description: "Slack mrkdwn message, max 2000 characters"
          required: true
          type: string
      steps:
        - name: Send Slack message
          env:
            SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          run: |
            if [ -z "$SLACK_WEBHOOK_URL" ]; then echo "SLACK_WEBHOOK_URL not configured; skipping"; exit 0; fi
            MESSAGE=$(jq -r '[.items[] | select(.type == "slack_notify") | .message][0] // empty' "$GH_AW_AGENT_OUTPUT" | head -c 2000)
            [ -n "$MESSAGE" ] || { echo "No message"; exit 0; }
            PAYLOAD=$(jq -n --arg text "$MESSAGE" '{text: $text}')
            curl -fsS --retry 3 -X POST -H 'Content-Type: application/json' -d "$PAYLOAD" "$SLACK_WEBHOOK_URL"
    teams-notify:
      description: "Post a short security summary to Microsoft Teams (Markdown subset; use blank lines between paragraphs)."
      runs-on: ubuntu-26.04
      output: "Teams notification sent"
      inputs:
        title:
          description: "Card title, max 120 characters"
          required: true
          type: string
        message:
          description: "Teams Markdown message, max 2000 characters"
          required: true
          type: string
      steps:
        - name: Send Teams message
          env:
            TEAMS_WEBHOOK_URL: ${{ secrets.TEAMS_WEBHOOK_URL }}
          run: |
            if [ -z "$TEAMS_WEBHOOK_URL" ]; then echo "TEAMS_WEBHOOK_URL not configured; skipping"; exit 0; fi
            ITEM=$(jq -c '[.items[] | select(.type == "teams_notify")][0] // empty' "$GH_AW_AGENT_OUTPUT")
            [ -n "$ITEM" ] || { echo "No message"; exit 0; }
            PAYLOAD=$(jq -n --argjson i "$ITEM" '{
              type: "message",
              attachments: [{
                contentType: "application/vnd.microsoft.card.adaptive",
                content: {
                  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                  type: "AdaptiveCard", version: "1.4",
                  body: [
                    {type: "TextBlock", size: "Medium", weight: "Bolder", wrap: true, text: ($i.title | .[0:120])},
                    {type: "TextBlock", wrap: true, text: ($i.message | .[0:2000])}
                  ]
                }
              }]
            }')
            curl -fsS --retry 3 -X POST -H 'Content-Type: application/json' -d "$PAYLOAD" "$TEAMS_WEBHOOK_URL"
---
