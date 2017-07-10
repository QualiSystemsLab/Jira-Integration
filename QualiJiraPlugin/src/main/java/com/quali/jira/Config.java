package com.quali.jira;

import com.atlassian.sal.api.pluginsettings.PluginSettings;
import com.atlassian.sal.api.pluginsettings.PluginSettingsFactory;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;

/**
 * Created by ericr on 7/6/2017.
 */
@XmlRootElement
@XmlAccessorType(XmlAccessType.FIELD)
public final class Config
{
    static void log1(String message) {
        try {
            FileWriter wr = new FileWriter("c:\\temp\\jiraplugin.txt", true);
            PrintWriter pw = new PrintWriter(wr);
            pw.printf("%s%n", message);
            pw.close();
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
    @XmlElement public String api_url;
    @XmlElement public String portal_url;
    @XmlElement public String csuser;
    @XmlElement public String cspass;
    @XmlElement public String jira_url;
    @XmlElement public String issue_type;
    @XmlElement public String project_name;
    @XmlElement public String support_domain;
    @XmlElement public String jira_username;
    @XmlElement public String jira_password;
    @XmlElement public String sandbox_minutes;

    private Config() { }
    public Config(PluginSettingsFactory pluginSettingsFactory) {
        loadFromPluginSettings(pluginSettingsFactory);
    }

    private void getset(PluginSettingsFactory pluginSettingsFactory, boolean iswrite) {
        PluginSettings pluginSettings = pluginSettingsFactory.createGlobalSettings();
        try {
            for (Field field : this.getClass().getDeclaredFields()) {
                log1("field: " + field.getName());
                for (Annotation a : field.getAnnotations()) {
                    if (a.annotationType().equals(XmlElement.class)) {
                        log1("found XmlElement annotation");
                        if (iswrite) {
                            Object val = field.get(this);
                            log1("storing field value to jira db: " + val);
                            pluginSettings.put("QUALI_PLUGIN_CONFIG." + field.getName(), val);
                        } else {
                            Object val = pluginSettings.get("QUALI_PLUGIN_CONFIG." + field.getName());
                            log1("loading field value from jira db: " + val);
                            field.set(this, val);
                        }
                    }
                }
            }
        } catch(IllegalAccessException e) {
            log1("illegal access exception");
            e.printStackTrace();
        }
    }
    public void writeToPluginSettings(PluginSettingsFactory pluginSettingsFactory) {
        getset(pluginSettingsFactory, true);
    }
    private void loadFromPluginSettings(PluginSettingsFactory pluginSettingsFactory) {
        getset(pluginSettingsFactory, false);
    }
}