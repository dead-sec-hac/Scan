@RestController
@RequestMapping("/test/async-activity")
public class AsyncActivityTestController {

@Autowired
private AdminConfig adminConfig;

@Autowired
private IAsyncActivityAdminService asyncActivityAdminService;

// Changed endpoint to "/rerun" for testing
@GetMapping("/rerun")
public ResponseEntity<String> reRunAsyncActivity(
@RequestParam("activityId") String activityId, // update in retool as well!
@RequestParam("asyncActivityKey") String asyncActivityKey)
throws UnauthorizedErrorException, IOException {

// Uncomment the following line if you want to enforce auth in tests
checkAuth(asyncActivityKey);
return asyncActivityAdminService.rerunExistingAsyncActivity(activityId);
}

private void checkAuth(String key) throws UnauthorizedErrorException {
if (StringUtils.isEmpty(key) || !key.equals(adminConfig.getAsyncActivityKey())) {
throw new UnauthorizedErrorException();
}
}
}
