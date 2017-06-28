package com.quali.jira.webwork;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.atlassian.jira.web.action.JiraWebActionSupport;

import java.net.URLEncoder;
import java.io.*;
import java.lang.Thread;

import java.net.HttpURLConnection;
import javax.net.ssl.HttpsURLConnection;
import java.net.URL;
import java.util.Properties;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.net.ssl.*;
import java.security.cert.*;

public class OpenInQualiCloudShell extends JiraWebActionSupport
{
    private static final Logger log = LoggerFactory.getLogger(OpenInQualiCloudShell.class);

    private String resid = "NoResid";
    private String qsoutput = "QSNoOutput";
    private String resource = "NoResource";
    private String resname = "NoReservationName";
    private String csdomain = "NoDomain";
    private String issueid = "NoIssueId";
    private int duration = 120;
    private String rawquery = "NoRawQuery";
    private String warnings = "";
    private String originaldomains = "NoOriginalDomains";

    private String apiip;
    private String portalip;
    private String apihttphttps;
    private String portalhttphttps;
    private String apiport;
    private String portalport;
    private String csuser;
    private String cspass;
    private String jira_url;
    private String issue_type;
    private String project_name;
    private String support_domain;
    private String jira_username;
    private String jira_password;

    public OpenInQualiCloudShell() {
        super();
        String f1 = "c:\\ProgramData\\QualiSystems\\QualiJiraPlugin.properties";
        String f2 = "/var/lib/quali/QualiJiraPlugin.properties";
        Properties prop = new Properties();
        InputStream input;
        try {
            try {
                input = new FileInputStream(f1);
            } catch(Exception e1) {
                input = new FileInputStream(f2);
            }
            prop.load(input);
        } catch (IOException ex) {
            warnings += "Failed to load " + f1 + " and " + f2 + ". Using CloudShell portal http://localhost:80 and sandbox API http://localhost:9000 admin/admin. Settings supported in QualiJiraPlugin.properties: api_host, portal_host, api_http_or_https, portal_http_or_https, api_port, portal_port, cloudshell_username, cloudshell_password";
            prop = new Properties();
        }
        apiip = prop.getProperty("api_host", "localhost");
        portalip = prop.getProperty("portal_host", "localhost");
        apihttphttps = prop.getProperty("api_http_or_https", "http");
        portalhttphttps = prop.getProperty("portal_http_or_https", "http");
        apiport = prop.getProperty("api_port", "82");
        portalport = prop.getProperty("portal_port", "80");
        csuser = prop.getProperty("cloudshell_username", "admin");
        cspass = prop.getProperty("cloudshell_password", "admin");

        jira_url = prop.getProperty("jira_url", "http://localhost:2990/jira");
        issue_type = prop.getProperty("issue_type", "Task");
        project_name = prop.getProperty("project_name", "");
        support_domain = prop.getProperty("support_domain", "Support");
        jira_username = prop.getProperty("jira_username", "admin");
        jira_password = prop.getProperty("jira_password", "admin");
    }

    private String http(String method, String url0, String body, String token) throws Exception {
        URL url = new URL(url0);
//        HostnameVerifier allHostsValid = new HostnameVerifier() {
//            public boolean verify(String hostname, SSLSession session) {
//                return true;
//            }
//        };
//        HttpsURLConnection.setDefaultHostnameVerifier(allHostsValid);
//        HttpURLConnection connection = (HttpURLConnection)url.openConnection();

        TrustManager[] trustAllCerts = new TrustManager[] { new X509TrustManager() {
            public java.security.cert.X509Certificate[] getAcceptedIssuers() { return null; }
            public void checkClientTrusted(X509Certificate[] certs, String authType) { }
            public void checkServerTrusted(X509Certificate[] certs, String authType) { }

        } };

        SSLContext sc = SSLContext.getInstance("SSL");
        sc.init(null, trustAllCerts, new java.security.SecureRandom());
        HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());

        // Create all-trusting host name verifier
        HostnameVerifier allHostsValid = new HostnameVerifier() {
            public boolean verify(String hostname, SSLSession session) { return true; }
        };
        // Install the all-trusting host verifier
        HttpsURLConnection.setDefaultHostnameVerifier(allHostsValid);

        HttpURLConnection connection = (HttpURLConnection)url.openConnection();
//        connection.setHostnameVerifier(allHostsValid);
        connection.setRequestMethod(method.toUpperCase());
        connection.setRequestProperty("Content-Length", ""+body.getBytes().length);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Accept", "application/json");
        if(token != null && token.length() > 0)
            connection.setRequestProperty("Authorization", "Basic " + token.trim());
        connection.setUseCaches (false);
        connection.setDoInput(true);
        if(body != null && body.length() > 0) {
            connection.setDoOutput(true);
            DataOutputStream wr = new DataOutputStream(connection.getOutputStream());
            wr.writeBytes(body);
            wr.flush();
            wr.close();
        }
        InputStream is = connection.getInputStream();
        BufferedReader rd = new BufferedReader(new InputStreamReader(is));
        StringBuilder response = new StringBuilder();
        for(;;) {
            String line = rd.readLine();
            if(line==null)
                break;
            response.append(line);
            response.append('\n');
        }
        rd.close();
        connection.disconnect();
        return response.toString();
    }

    @Override
    public String execute() throws Exception {
        rawquery = java.net.URLDecoder.decode(getHttpRequest().getQueryString(), "UTF-8");
        {
            Pattern pattern = Pattern.compile("QS_RESOURCE[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                qsoutput = "QS_RESOURCE(resource name) not found in issue description";
                return super.execute();
            }
            resource = matcher.group(1);
        }
        {
            Pattern pattern = Pattern.compile("QS_DOMAIN[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                qsoutput = "QS_DOMAIN(domain name) not found in issue description";
                return super.execute();
            }
            csdomain = matcher.group(1);
        }
        {
            Pattern pattern = Pattern.compile("QS_ORIGINAL_DOMAINS[(]([^)]*)[)]");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                qsoutput = "QS_ORIGINAL_DOMAINS(domain name) not found in issue description";
                return super.execute();
            }
            originaldomains = matcher.group(1);
        }
        {
            Pattern pattern = Pattern.compile("issueid=([^&]*)");
            Matcher matcher = pattern.matcher(rawquery);
            if(!matcher.find()) {
                issueid = "Issue ID missing from URL";
                return super.execute();
            }
            issueid = matcher.group(1);
        }
        resname = resource + " debug session - issue " + issueid;

        String token = "";
        try {
            String url = apihttphttps + "://" + apiip + ":" + apiport + "/api/login";
            String body = "{  \"username\": \"" + csuser + "\",  \"password\": \"" + cspass + "\",   \"domain\": \"" + csdomain + "\"}";
            qsoutput = url + "\n" + body + "\n";
            String s = http("PUT", url, body, null);
            token = s.replaceAll("\"", "");
        } catch(Exception e) {
            qsoutput += "Failed to log in to CloudShell sandbox API: " + e.toString();
            return super.execute();
        }

//        try {
//            String url = apihttphttps + "://" + apiip + ":" + apiport + "/api/v2/blueprints/" +
////                    URLEncoder.encode(bpname, "UTF-8").replaceAll("[+]", "%20")
//                    bpname.replaceAll(" ", "%20")
//                    + "/start";
//            String body = "{  \"duration\": \"PT23H\",  \"name\": \"" + resname + "\"  }";
//            String s = http("POST", url, body, token);
//            qsoutput = url + "\n" + body + "\n" + s;
//            Pattern pattern = Pattern.compile("\"id\":\"([^\"]*)\"");
//            Matcher matcher = pattern.matcher(s);
//            if(!matcher.find()) {
//                qsoutput = "Failed to create reservation: " + s;
//                return super.execute();
//            }
//            resid = matcher.group(1);
//        } catch(Exception e) {
//            qsoutput = "Failed to create reservation: " + e.toString();
//            return super.execute();
//        }
        String workerresid;
        try {
            String url = apihttphttps + "://" + apiip + ":" + apiport + "/api/v2/blueprints/JiraSupport/start";
            String body = "{  \"duration\": \"PT5M\",  \"name\": \"jiraworker\"  }";
            String s = http("POST", url, body, token);
            qsoutput = url + "\n" + body + "\n" + s;
            Pattern pattern = Pattern.compile("\"id\":\"([^\"]*)\"");
            Matcher matcher = pattern.matcher(s);
            if(!matcher.find()) {
                qsoutput = "Failed to create reservation: " + s;
                return super.execute();
            }
            workerresid = matcher.group(1);
        } catch(Exception e) {
            qsoutput = "Failed to create reservation: " + e.toString();
            return super.execute();
        }
        String executionid;
        try {
            String url = apihttphttps + "://" + apiip + ":" + apiport + "/api/v2/sandboxes/"+workerresid+"/commands/CreateJiraSandbox/start";
            String body = "{ \"params\": [";

            body += "{\"name\":\"reservation_name\",\"value\":\""+resname+"\"}, ";
            body += "{\"name\":\"resource_name\",\"value\":\""+resource+"\"}, ";
            body += "{\"name\":\"duration_in_minutes\",\"value\":\"120\"}, ";
            body += "{\"name\":\"user\", \"value\":\""+csuser+"\"}, ";

            body += "{\"name\":\"jira_url\", \"value\":\""+jira_url+"\"}, ";
            body += "{\"name\":\"issue_type\", \"value\":\""+issue_type+"\"}, ";
            body += "{\"name\":\"project_name\", \"value\":\""+project_name+"\"}, ";
            body += "{\"name\":\"support_domain\", \"value\":\""+support_domain+"\"}, ";
            body += "{\"name\":\"jira_username\", \"value\":\""+jira_username+"\"}, ";
            body += "{\"name\":\"jira_password\", \"value\":\""+jira_password+"\"} ";
            body += "], \"printOutput\": true }";
            qsoutput = url + "\n" + body + "\n";

            String s = http("POST", url, body, token);
            qsoutput += s;
            Pattern pattern = Pattern.compile("/executions/([^\"]*)\"");
            Matcher matcher = pattern.matcher(s);
            if(!matcher.find()) {
                qsoutput += "Failed to get CreateJiraSandbox execution id: " + s;
                return super.execute();
            }
            executionid = matcher.group(1);
        } catch(Exception e) {
            qsoutput += "Failed to run CreateJiraSandbox: " + e.toString();
            return super.execute();
        }

        for(int i=0;i<5;i++) {
            try {
                String url = apihttphttps + "://" + apiip + ":" + apiport + "/api/v2/executions/" + executionid;
                String s = http("GET", url, "", token);
                qsoutput = url + "\n" + s;
                if(s.replaceAll(" ", "").contains("\"status\":\"Completed\"")) {
                    Pattern pattern = Pattern.compile("\"output\":\"([^\"]*)\"");
                    Matcher matcher = pattern.matcher(s);
                    if(!matcher.find()) {
                        qsoutput = "Output not extracted: " + s;
                        return super.execute();
                    }
                    resid = matcher.group(1);
                    resid = resid.replace('\\', ' ').replaceAll(" r n", "");
                    break;
                }
                if(s.replaceAll(" ", "").contains("\"status\":\"Failed\"") || s.replaceAll(" ", "").contains("\"status\":\"Error\"")) {
                    qsoutput = "CreateJiraSandbox failed: " + s;
                    break;
                }
                Thread.sleep(5000);

            } catch (Exception e) {
                qsoutput = "CreateJiraSandbox failed: " + e.toString();
                return super.execute();
            }
        }

        try {
            String url = apihttphttps + "://" + apiip + ":" + apiport + "/api/v2/sandboxes/"+workerresid+"/stop";
            qsoutput = url + "\n";
            String s = http("POST", url, "", token);
            qsoutput += s;
        } catch(Exception e) {
            qsoutput += "Warning: Failed to stop jiraworker sandbox: " + e.toString();
            return super.execute();
        }
        qsoutput = "";
        return super.execute(); //returns SUCCESS
    }
    public String getQSOutput() {
        return qsoutput;
    }
    public String getPortalhttphttps() {
        return portalhttphttps;
    }
    public String getPortalport() {
        return portalport;
    }
    public String getPortalip() {
        return portalip;
    }
    public String getResid() {
        return resid;
    }
    public String getResname() {
        return resname;
    }
    public String getResource() {
        return resource;
    }
    public String getRawquery() {
        return rawquery;
    }
    public String getWarning() {
        return warnings;
    }
    public String getError() {
        if(resid.equals("NoResId"))
            return "FAILED TO CREATE RESERVATION";
        return "";
    }
}
