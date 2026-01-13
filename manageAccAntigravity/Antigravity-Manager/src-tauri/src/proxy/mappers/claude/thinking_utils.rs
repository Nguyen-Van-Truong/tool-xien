use super::models::{Message, MessageContent, ContentBlock};
use tracing::info;

#[derive(Debug, Default)]
pub struct ConversationState {
    pub in_tool_loop: bool,
    pub interrupted_tool: bool,
    pub last_assistant_idx: Option<usize>,
}

/// Analyze the conversation to detect tool loops or interrupted tool calls
pub fn analyze_conversation_state(messages: &[Message]) -> ConversationState {
    let mut state = ConversationState::default();
    
    if messages.is_empty() {
        return state;
    }

    // Find last assistant message index
    for (i, msg) in messages.iter().enumerate().rev() {
        if msg.role == "assistant" {
            state.last_assistant_idx = Some(i);
            break;
        }
    }

    // Check if the very last message is a Tool Result (User role with ToolResult block)
    if let Some(last_msg) = messages.last() {
        if last_msg.role == "user" {
           if let MessageContent::Array(blocks) = &last_msg.content {
               if blocks.iter().any(|b| matches!(b, ContentBlock::ToolResult { .. })) {
                   state.in_tool_loop = true;
               }
           }
        }
    }

    // Check for interrupted tool: Last assistant message has ToolUse, but no corresponding ToolResult in next user msg
    // (This is harder to detect perfectly on a stateless request, but usually if we are 
    //  in a state where we have ToolUse but the conversation seems "broken" or stripped)
    // Actually, in the proxy context, we typically see:
    // ... Assistant (ToolUse) -> User (ToolResult) : Normal Loop
    // ... Assistant (ToolUse) -> User (Text) : Interrupted (User cancelled)

    // For "Thinking Utils", we care about the case where valid signatures are missing.
    // If we are in a tool loop (last msg is ToolResult), and the *preceding* Assistant message
    // had its Thinking block stripped (due to invalid sig), then we are in a "Broken Tool Loop".
    // Gemini/Claude will reject a ToolResult if the preceding Assistant message didn't start with Thinking.
    
    state
}

/// Recover from broken tool loops by injecting synthetic messages
/// 
/// When client strips valid thinking blocks (leaving only ToolUse), and we are in a tool loop,
/// the API will reject the request because "Assistant message must start with thinking".
/// We cannot fake the signature.
/// Solution: Close the loop artificially so the model starts fresh.
pub fn close_tool_loop_for_thinking(messages: &mut Vec<Message>) {
    let state = analyze_conversation_state(messages);
    
    if !state.in_tool_loop {
        return;
    }
    
    // Check if the last assistant message has a thinking block
    let mut has_thinking = false;
    if let Some(idx) = state.last_assistant_idx {
        if let Some(msg) = messages.get(idx) {
             if let MessageContent::Array(blocks) = &msg.content {
                 has_thinking = blocks.iter().any(|b| matches!(b, ContentBlock::Thinking { .. }));
             }
        }
    }

    // If we are in a tool loop BUT the assistant message has no thinking block (it was stripped or missing),
    // we must break the loop. 
    // Exception: If thinking is NOT enabled for this request, we don't need to do this (handled by other logic).
    // But here we assume we are called because thinking IS enabled.
    if !has_thinking {
        info!("[Thinking-Recovery] Detected broken tool loop (ToolResult without preceding Thinking). Injecting synthetic messages.");
        
        // Strategy: 
        // 1. Inject a "fake" Assistant message saying "Tool execution completed."
        // 2. Inject a "fake" User message saying "[Continue]"
        // This pushes the problematic ToolUse/ToolResult pair into history that is "closed" 
        // and forces the model to generate a NEW turn, which will start with a fresh Thinking block.
        
        // Wait, simply appending messages might not work if the API expects strict alternation.
        // If the last message IS ToolResult (User), we can append Assistant -> User.
        
        messages.push(Message {
            role: "assistant".to_string(),
            content: MessageContent::Array(vec![
                ContentBlock::Text { text: "[Tool execution completed. Please proceed.]".to_string() }
            ])
        });
        messages.push(Message {
            role: "user".to_string(),
            content: MessageContent::Array(vec![
                ContentBlock::Text { text: "Proceed.".to_string() }
            ])
        });
    }
}
