#include "includes.h"

/*
 * Computes the time difference between two timeb structures
 */
void timeDiff(struct timeb start, struct timeb end, struct timeb *result) 
{
	result->time = end.time - start.time;
	result->millitm = end.millitm - start.millitm;
}
