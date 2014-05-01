#include "includes.h"

/*
 * Computes the time difference between two timeb structures
 */
void timeDiff(struct timeb start, struct timeb end, struct timeb *result) 
{
	result->time = end.time - start.time;
	result->millitm = end.millitm - start.millitm;
}

/*
 * Compares if 2 strings match each other
 */
int match_str(const char *s1, const char *s2) {
	return !strncmp(s1, s2, strlen(s2));
}



