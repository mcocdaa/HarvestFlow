export const truncateString = (str: string, startLength = 8, endLength = 4): string => {
  if (str.length <= startLength + endLength + 3) {
    return str;
  }
  return `${str.substring(0, startLength)}...${str.substring(str.length - endLength)}`;
};

export const truncateSessionId = (sessionId: string): string => {
  return truncateString(sessionId, 12, 4);
};
